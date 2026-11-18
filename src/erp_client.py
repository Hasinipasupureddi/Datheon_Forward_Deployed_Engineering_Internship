import os
import time
import requests

ERP_API_URL = os.getenv("ERP_API_URL", "http://127.0.0.1:8001").rstrip("/")
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ERPClientError(Exception):
    """Raised when the ERP/CRM service cannot complete a request."""


class ERPClient:
    def __init__(self, base_url=None, timeout=5, max_attempts=3):
        self.base_url = (base_url or ERP_API_URL).rstrip("/")
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.session = requests.Session()

    def _request(self, method, path, payload=None):
        url = f"{self.base_url}{path}"

        # GET and PATCH are safe to retry for this mock service.
        attempts = self.max_attempts if method in {"GET", "PATCH"} else 1

        for attempt in range(attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt < attempts - 1:
                        time.sleep(0.5 * (2 ** attempt))
                        continue

                if not response.ok:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text

                    raise ERPClientError(
                        f"ERP API returned {response.status_code}: {detail}"
                    )

                return response.json()

            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt == attempts - 1:
                    raise ERPClientError(
                        f"ERP API connection failed after {attempts} attempt(s): {exc}"
                    ) from exc

                time.sleep(0.5 * (2 ** attempt))

        raise ERPClientError("ERP API request failed.")

    def inventory_lookup(self, sku):
        return self._request("GET", f"/inventory/{sku}")

    def get_lead(self, lead_id):
        return self._request("GET", f"/leads/{lead_id}")

    def update_lead_status(self, lead_id, status):
        return self._request(
            "PATCH",
            f"/leads/{lead_id}/status",
            {"status": status},
        )

    def create_ticket(self, subject, description, priority="medium"):
        return self._request(
            "POST",
            "/tickets",
            {
                "subject": subject,
                "description": description,
                "priority": priority,
            },
        )

    def list_tickets(self):
        return self._request("GET", "/tickets")


erp_client = ERPClient()
