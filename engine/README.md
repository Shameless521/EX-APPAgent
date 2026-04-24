# appagent-engine

Python data engine for EX-APPAgent.

It collects app metrics, reviews, ASO rankings, competitor public data, budget logs, experiment pre-calculations, and health status files for the EX-APPAgent skill/plugin layer.

## CLI

```bash
uv run appagent --version
uv run appagent collect
uv run appagent health
```

## Configuration

Runtime configuration is read from `~/.appagent/config.json` and registered apps from `~/.appagent/apps.json`.

Google Play revenue, downloads, ratings, and bulk review history use Google Play Console reports stored in the private Cloud Storage bucket shown in Play Console > Download reports. Configure it as:

```json
{
  "google_play": {
    "service_account_path": "/path/to/service-account.json",
    "reports_bucket": "pubsite_prod_rev_01234567890987654321"
  }
}
```

The service account needs Play Console permissions for the selected report types and Cloud Storage read access to the report bucket. Network requests honor `HTTPS_PROXY`, `HTTP_PROXY`, `https_proxy`, and `http_proxy`.
