import requests

class APIError(Exception):
    pass

class VidyaAPI:
    """Thin client for Vidya's existing authenticated RAG API."""
    def __init__(self, base_url: str, access_token: str, timeout: int = 90):
        self.base_url = (base_url or "").rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        if not self.base_url:
            raise APIError("RAG_API_URL is not configured.")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}))
        try:
            response = requests.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise APIError(f"Cannot reach Vidya RAG API: {exc}") from exc
        try:
            payload = response.json()
        except ValueError:
            payload = {"error": response.text[:1000]}
        if not response.ok:
            detail = payload.get("error") or payload.get("message") or response.reason
            raise APIError(f"HTTP {response.status_code}: {detail}")
        return payload

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, payload):
        return self._request("POST", path, json=payload)

    def upload(self, path, uploaded_file, metadata):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }
        # Existing backend must accept multipart field "file" and JSON metadata field.
        data = {"metadata": __import__("json").dumps(metadata)}
        return self._request("POST", path, files=files, data=data)
