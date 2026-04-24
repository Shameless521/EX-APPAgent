"""App Store Connect API collector — auth, sales reports, ratings."""

from __future__ import annotations

import gzip
import io
import time
from csv import DictReader
from datetime import date, timedelta

import httpx
import jwt

from appagent_engine.config import AppStoreConnectConfig
from appagent_engine.net import with_retry

BASE_URL = "https://api.appstoreconnect.apple.com"


class AppStoreConnectClient:
    """Authenticated client for App Store Connect API."""

    def __init__(self, config: AppStoreConnectConfig):
        self._config = config
        self._token: str | None = None
        self._token_expiry: float = 0

    def _generate_token(self) -> str:
        """Generate a JWT token (ES256, 20-minute expiry)."""
        now = time.time()
        payload = {
            "iss": self._config.issuer_id,
            "iat": int(now),
            "exp": int(now + 20 * 60),
            "aud": "appstoreconnect-v1",
        }
        token = jwt.encode(
            payload,
            self._config.private_key,
            algorithm="ES256",
            headers={"kid": self._config.key_id},
        )
        self._token = token
        self._token_expiry = now + 19 * 60  # Refresh 1 min early
        return token

    @property
    def token(self) -> str:
        if self._token is None or time.time() >= self._token_expiry:
            return self._generate_token()
        return self._token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, url: str, **kwargs) -> httpx.Response:
        def _request() -> httpx.Response:
            with httpx.Client(timeout=30) as client:
                resp = client.get(url, headers=self._headers, **kwargs)
                resp.raise_for_status()
                return resp

        return with_retry(_request, attempts=3)

    # --- Sales & Trends Reports ---

    def fetch_sales_report(
        self,
        report_date: date | None = None,
        report_type: str = "SALES",
        report_sub_type: str = "SUMMARY",
        frequency: str = "DAILY",
    ) -> list[dict]:
        """Fetch sales report. Defaults to T-2 date (App Store data delay)."""
        if report_date is None:
            report_date = date.today() - timedelta(days=2)

        if not self._config.vendor_number:
            raise ValueError(
                "vendor_number is required for sales reports. "
                "Find it in App Store Connect → Payments and Financial Reports. "
                "Add it to ~/.appagent/config.json under appstore_connect.vendor_number"
            )

        url = f"{BASE_URL}/v1/salesReports"
        params = {
            "filter[reportType]": report_type,
            "filter[reportSubType]": report_sub_type,
            "filter[frequency]": frequency,
            "filter[reportDate]": report_date.strftime("%Y-%m-%d"),
            "filter[vendorNumber]": self._config.vendor_number,
        }

        # Sales reports return gzipped TSV
        resp = self._get(url, params=params)

        if resp.headers.get("content-encoding") == "gzip" or resp.content[:2] == b"\x1f\x8b":
            text = gzip.decompress(resp.content).decode("utf-8")
        else:
            text = resp.text

        return self._parse_tsv(text)

    def fetch_subscription_report(self, report_date: date | None = None) -> list[dict]:
        """Fetch subscription event report."""
        if report_date is None:
            report_date = date.today() - timedelta(days=2)

        url = f"{BASE_URL}/v1/salesReports"
        params = {
            "filter[reportType]": "SUBSCRIPTION_EVENT",
            "filter[reportSubType]": "SUMMARY",
            "filter[frequency]": "DAILY",
            "filter[reportDate]": report_date.strftime("%Y-%m-%d"),
            "filter[vendorNumber]": self._config.vendor_number,
        }

        resp = self._get(url, params=params)
        if resp.content[:2] == b"\x1f\x8b":
            text = gzip.decompress(resp.content).decode("utf-8")
        else:
            text = resp.text

        return self._parse_tsv(text)

    @staticmethod
    def _parse_tsv(text: str) -> list[dict]:
        """Parse Tab-Separated Values into list of dicts."""
        reader = DictReader(io.StringIO(text), delimiter="\t")
        return list(reader)

    # --- App Info & Ratings ---

    def fetch_app_info(self, bundle_id: str) -> dict | None:
        """Fetch app details by bundle ID."""
        url = f"{BASE_URL}/v1/apps"
        params = {"filter[bundleId]": bundle_id}
        resp = self._get(url, params=params)
        data = resp.json()
        apps = data.get("data", [])
        return apps[0] if apps else None

    def fetch_ratings(self, app_id: str) -> dict:
        """Fetch app ratings summary (requires app_id from fetch_app_info)."""
        url = f"{BASE_URL}/v1/apps/{app_id}/appStoreVersions"
        params = {"include": "appStoreVersionLocalizations"}
        resp = self._get(url, params=params)
        return resp.json()

    # --- Customer Reviews ---

    def fetch_reviews(self, app_id: str, limit: int = 50) -> list[dict]:
        """Fetch customer reviews for an app."""
        url = f"{BASE_URL}/v1/apps/{app_id}/customerReviews"
        params = {
            "limit": min(limit, 200),
            "sort": "-createdDate",
        }
        resp = self._get(url, params=params)
        data = resp.json()
        reviews = []
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            reviews.append({
                "id": item["id"],
                "rating": attrs.get("rating"),
                "title": attrs.get("title"),
                "body": attrs.get("body"),
                "reviewer": attrs.get("reviewerNickname"),
                "date": attrs.get("createdDate"),
                "territory": attrs.get("territory"),
            })
        return reviews

    # --- Helpers ---

    def get_app_id(self, bundle_id: str) -> str | None:
        """Get the numeric app ID from bundle ID."""
        info = self.fetch_app_info(bundle_id)
        return info["id"] if info else None

    def collect_daily_metrics(
        self,
        bundle_id: str,
        report_date: date | None = None,
    ) -> dict:
        """Collect all daily metrics for one app, return standardized dict."""
        if report_date is None:
            report_date = date.today() - timedelta(days=2)

        # Resolve Apple Identifier for reliable filtering
        apple_id = self.get_app_id(bundle_id)

        # Fetch sales report (returns ALL apps under this vendor)
        sales_rows = self.fetch_sales_report(report_date=report_date)

        revenue = 0.0
        downloads = 0
        updates = 0

        for row in sales_rows:
            # Filter: only count rows matching this specific app
            row_apple_id = row.get("Apple Identifier", "").strip()
            row_sku = row.get("SKU", "").strip()

            match = False
            if apple_id and row_apple_id == apple_id:
                match = True
            elif row_sku == bundle_id:
                match = True

            if not match:
                continue

            units = int(row.get("Units", 0))
            product_type = row.get("Product Type Identifier", "")

            # Type 1 = free/paid download, 1F = free, 1T = paid
            if product_type in ("1", "1F", "1T"):
                downloads += units
            elif product_type == "7":  # Update
                updates += units

            # Revenue = Developer Proceeds * Units
            proceeds = float(row.get("Developer Proceeds", 0))
            revenue += proceeds * units

        return {
            "date": report_date.isoformat(),
            "source": "appstore_connect",
            "revenue": round(revenue, 2),
            "downloads": downloads,
            "updates": updates,
        }
