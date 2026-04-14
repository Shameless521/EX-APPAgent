"""Google Play Developer API collector — auth, reports, reviews."""

from __future__ import annotations

import os
from datetime import date, timedelta
from urllib.parse import urlparse

from appagent_engine.config import GooglePlayConfig


def _build_proxy_http():
    """Build an httplib2.Http with proxy from environment variables."""
    import httplib2

    # Read proxy from env (prefer https_proxy, fallback to http_proxy)
    proxy_url = os.environ.get("https_proxy") or os.environ.get("http_proxy") or \
                os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    if not proxy_url:
        return httplib2.Http(timeout=60)

    parsed = urlparse(proxy_url)
    proxy_type = httplib2.socks.PROXY_TYPE_HTTP
    if parsed.scheme in ("socks5", "socks5h"):
        proxy_type = httplib2.socks.PROXY_TYPE_SOCKS5
    elif parsed.scheme in ("socks4", "socks4a"):
        proxy_type = httplib2.socks.PROXY_TYPE_SOCKS4

    proxy_info = httplib2.ProxyInfo(
        proxy_type=proxy_type,
        proxy_host=parsed.hostname or "127.0.0.1",
        proxy_port=parsed.port or 1080,
        proxy_user=parsed.username,
        proxy_pass=parsed.password,
    )
    return httplib2.Http(proxy_info=proxy_info, timeout=60)


class GooglePlayClient:
    """Authenticated client for Google Play Developer API."""

    def __init__(self, config: GooglePlayConfig):
        self._config = config
        self._service = None

    def _get_service(self):
        """Build or return cached androidpublisher service."""
        if self._service is not None:
            return self._service

        from google.oauth2 import service_account
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_info(
            self._config.service_account_info,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )

        http = _build_proxy_http()
        authorized_http = AuthorizedHttp(credentials, http=http)
        self._service = build(
            "androidpublisher", "v3",
            http=authorized_http,
            num_retries=3,
        )
        return self._service

    # --- Reviews ---

    def fetch_reviews(self, package_name: str) -> list[dict]:
        """Fetch recent reviews for a package."""
        service = self._get_service()
        result = service.reviews().list(packageName=package_name).execute()
        return result.get("reviews", [])

    # --- Sales / Monetization Reports ---

    def fetch_monthly_report(
        self,
        package_name: str,
        year: int | None = None,
        month: int | None = None,
    ) -> bytes | None:
        """Download monthly earnings report from GCS bucket.

        Google Play financial reports are exported as CSV to a GCS bucket.
        Reports are auto-generated monthly, available ~30 days after month end.
        """
        if year is None or month is None:
            today = date.today()
            target = today.replace(day=1) - timedelta(days=60)
            year = target.year
            month = target.month

        # Google Play monthly reports require GCS bucket access
        # Will be enhanced when GCS access is configured
        return None

    def collect_daily_metrics(
        self,
        package_name: str,
        report_date: date | None = None,
    ) -> dict:
        """Collect available metrics for one Android app.

        Note: Google Play doesn't provide real-time daily revenue via API.
        Revenue data comes from monthly CSV reports with ~30 day delay.
        We collect what's available in real-time: reviews and ratings.
        """
        if report_date is None:
            report_date = date.today() - timedelta(days=1)

        reviews = self.fetch_reviews(package_name)
        new_reviews = 0
        total_rating = 0.0
        rating_count = 0

        for r in reviews:
            comments = r.get("comments", [])
            if comments:
                user_comment = comments[0].get("userComment", {})
                star = user_comment.get("starRating", 0)
                if star > 0:
                    total_rating += star
                    rating_count += 1
                new_reviews += 1

        avg_rating = round(total_rating / rating_count, 1) if rating_count else None

        return {
            "date": report_date.isoformat(),
            "source": "google_play",
            "revenue": 0,
            "downloads": 0,
            "reviews_count": new_reviews,
            "avg_rating": avg_rating,
        }

    # --- App Details ---

    def fetch_app_details(self, package_name: str) -> dict | None:
        """Fetch app listing details."""
        service = self._get_service()
        try:
            result = service.edits().insert(
                packageName=package_name, body={}
            ).execute()
            edit_id = result["id"]

            details = service.edits().details().get(
                packageName=package_name, editId=edit_id
            ).execute()

            service.edits().delete(
                packageName=package_name, editId=edit_id
            ).execute()

            return details
        except Exception:
            return None
