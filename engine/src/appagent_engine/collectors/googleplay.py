"""Google Play Developer API collector — auth, reports, reviews."""

from __future__ import annotations

import os
import csv
import io
import zipfile
from datetime import date, timedelta
from urllib.parse import urlparse

from appagent_engine.config import GooglePlayConfig
from appagent_engine.net import classify_error, with_retry

ANDROIDPUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
DEVSTORAGE_READ_SCOPE = "https://www.googleapis.com/auth/devstorage.read_only"


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
        self._storage_service = None

    def _get_credentials(self):
        from google.oauth2 import service_account

        return service_account.Credentials.from_service_account_info(
            self._config.service_account_info,
            scopes=[ANDROIDPUBLISHER_SCOPE, DEVSTORAGE_READ_SCOPE],
        )

    def _get_service(self):
        """Build or return cached androidpublisher service."""
        if self._service is not None:
            return self._service

        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        http = _build_proxy_http()
        authorized_http = AuthorizedHttp(self._get_credentials(), http=http)
        self._service = build(
            "androidpublisher", "v3",
            http=authorized_http,
            num_retries=3,
        )
        return self._service

    def _get_storage_service(self):
        """Build or return cached Google Cloud Storage service."""
        if self._storage_service is not None:
            return self._storage_service

        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        http = _build_proxy_http()
        authorized_http = AuthorizedHttp(self._get_credentials(), http=http)
        self._storage_service = build(
            "storage", "v1",
            http=authorized_http,
            num_retries=3,
        )
        return self._storage_service

    # --- Reviews ---

    def fetch_reviews(self, package_name: str) -> list[dict]:
        """Fetch recent reviews for a package."""
        service = self._get_service()
        result = with_retry(
            lambda: service.reviews().list(packageName=package_name).execute(num_retries=3),
            attempts=3,
        )
        return result.get("reviews", [])

    # --- Sales / Monetization Reports ---

    def fetch_monthly_report(
        self,
        package_name: str,
        year: int | None = None,
        month: int | None = None,
        report_type: str = "sales",
        dimension: str = "overview",
    ) -> bytes | None:
        """Download a monthly Google Play report from the configured GCS bucket.

        Supported report_type values:
        - sales: sales/salesreport_YYYYMM.zip
        - earnings: earnings/earnings_YYYYMM.zip
        - installs: stats/installs/installs_PACKAGE_YYYYMM_overview.csv
        - ratings: stats/ratings/ratings_PACKAGE_YYYYMM_overview.csv
        """
        if year is None or month is None:
            today = date.today()
            target = today.replace(day=1) - timedelta(days=60)
            year = target.year
            month = target.month

        bucket = self._config.normalized_reports_bucket
        if not bucket:
            return None

        object_name = _report_object_name(package_name, year, month, report_type, dimension)
        storage = self._get_storage_service()
        return with_retry(
            lambda: storage.objects().get_media(bucket=bucket, object=object_name).execute(num_retries=3),
            attempts=3,
        )

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
        report_status: dict[str, str] = {}

        downloads = None
        rating = avg_rating
        revenue = None
        active_subscriptions = None

        if self._config.normalized_reports_bucket:
            revenue = self._collect_sales_for_date(package_name, report_date, report_status)
            downloads = self._collect_installs_for_date(package_name, report_date, report_status)
            report_rating = self._collect_rating_for_date(package_name, report_date, report_status)
            if report_rating is not None:
                rating = report_rating
            # Reserved for the financial-stats subscriptions report. Kept as
            # explicit None until a product_id is configured.
            active_subscriptions = None
        else:
            report_status["reports_bucket"] = "not_configured"

        missing = [
            name for name, value in {
                "revenue": revenue,
                "downloads": downloads,
            }.items() if value is None
        ]

        return {
            "date": report_date.isoformat(),
            "source": "google_play",
            "revenue": revenue,
            "downloads": downloads,
            "reviews_count": new_reviews,
            "avg_rating": rating,
            "ratings_count": rating_count or None,
            "active_subscriptions": active_subscriptions,
            "report_status": report_status,
            "data_complete": not missing,
            "missing_fields": missing,
        }

    def _collect_sales_for_date(self, package_name: str, report_date: date, status: dict[str, str]) -> float | None:
        raw = None
        for report_type in ("earnings", "sales"):
            try:
                raw = self.fetch_monthly_report(
                    package_name,
                    report_date.year,
                    report_date.month,
                    report_type=report_type,
                )
                if raw:
                    status[report_type] = "ok"
                    break
            except Exception as exc:
                status[report_type] = f"{classify_error(exc)}: {exc}"

        if not raw:
            return None

        rows = _decode_report_rows(raw)
        return _sum_sales_revenue(rows, package_name, report_date)

    def _collect_installs_for_date(self, package_name: str, report_date: date, status: dict[str, str]) -> int | None:
        try:
            raw = self.fetch_monthly_report(
                package_name,
                report_date.year,
                report_date.month,
                report_type="installs",
            )
        except Exception as exc:
            status["installs"] = f"{classify_error(exc)}: {exc}"
            return None

        if not raw:
            return None
        status["installs"] = "ok"
        rows = _decode_report_rows(raw)
        return _daily_installs(rows, package_name, report_date)

    def _collect_rating_for_date(self, package_name: str, report_date: date, status: dict[str, str]) -> float | None:
        try:
            raw = self.fetch_monthly_report(
                package_name,
                report_date.year,
                report_date.month,
                report_type="ratings",
            )
        except Exception as exc:
            status["ratings"] = f"{classify_error(exc)}: {exc}"
            return None

        if not raw:
            return None
        status["ratings"] = "ok"
        rows = _decode_report_rows(raw)
        return _daily_rating(rows, package_name, report_date)

    # --- App Details ---

    def fetch_app_details(self, package_name: str) -> dict | None:
        """Fetch app listing details."""
        service = self._get_service()
        try:
            result = with_retry(
                lambda: service.edits().insert(
                    packageName=package_name, body={}
                ).execute(num_retries=3),
                attempts=3,
            )
            edit_id = result["id"]

            details = with_retry(
                lambda: service.edits().details().get(
                    packageName=package_name, editId=edit_id
                ).execute(num_retries=3),
                attempts=3,
            )

            with_retry(
                lambda: service.edits().delete(
                    packageName=package_name, editId=edit_id
                ).execute(num_retries=3),
                attempts=3,
            )

            return details
        except Exception:
            return None


def _report_object_name(
    package_name: str,
    year: int,
    month: int,
    report_type: str,
    dimension: str,
) -> str:
    ym = f"{year:04d}{month:02d}"
    if report_type == "sales":
        return f"sales/salesreport_{ym}.zip"
    if report_type == "earnings":
        return f"earnings/earnings_{ym}.zip"
    if report_type == "installs":
        return f"stats/installs/installs_{package_name}_{ym}_{dimension}.csv"
    if report_type == "ratings":
        return f"stats/ratings/ratings_{package_name}_{ym}_{dimension}.csv"
    raise ValueError(f"Unsupported Google Play report_type: {report_type}")


def _decode_report_rows(raw: bytes) -> list[dict]:
    """Decode zipped or plain CSV report bytes into row dicts."""
    csv_payloads: list[bytes] = []
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".csv"):
                    csv_payloads.append(zf.read(name))
    else:
        csv_payloads.append(raw)

    rows: list[dict] = []
    for payload in csv_payloads:
        text = _decode_text(payload)
        sample = text[:2048]
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows.extend({(k or "").strip(): v for k, v in row.items()} for row in reader)
    return rows


def _decode_text(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _sum_sales_revenue(rows: list[dict], package_name: str, report_date: date) -> float | None:
    total = 0.0
    seen = False
    report_date_str = report_date.isoformat()
    for row in rows:
        row_package = _first(row, "Package ID", "Package Name", "Product ID", "Package")
        if row_package and row_package != package_name:
            continue

        row_date = _first(row, "Order Charged Date", "Transaction Date", "Date")
        if row_date and row_date[:10] != report_date_str:
            continue

        amount = _first_number(
            row,
            "Developer Proceeds",
            "Amount (Merchant Currency)",
            "Charged Amount",
            "Item Price",
            "Amount",
        )
        if amount is None:
            continue

        status = _first(row, "Financial Status", "Transaction Type").lower()
        if "refund" in status or "chargeback" in status:
            amount = -abs(amount)

        total += amount
        seen = True

    return round(total, 2) if seen else None


def _daily_installs(rows: list[dict], package_name: str, report_date: date) -> int | None:
    report_date_str = report_date.isoformat()
    for row in rows:
        row_package = _first(row, "Package Name", "Package ID", "Package")
        if row_package and row_package != package_name:
            continue
        if _first(row, "Date") != report_date_str:
            continue
        value = _first_number(
            row,
            "Daily User Installs",
            "Daily Device Installs",
            "Store Listing Acquisitions",
            "Installers",
        )
        return int(value) if value is not None else None
    return None


def _daily_rating(rows: list[dict], package_name: str, report_date: date) -> float | None:
    report_date_str = report_date.isoformat()
    for row in rows:
        row_package = _first(row, "Package Name", "Package ID", "Package")
        if row_package and row_package != package_name:
            continue
        if _first(row, "Date") != report_date_str:
            continue
        value = _first_number(row, "Total Average Rating", "Daily Average Rating")
        return round(value, 2) if value is not None else None
    return None


def _first(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _first_number(row: dict, *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        cleaned = str(value).strip().replace(",", "")
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch in ".-")
        try:
            return float(cleaned)
        except ValueError:
            continue
    return None
