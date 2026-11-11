import requests
from dataclasses import dataclass
from typing import Any

REQUEST_TIMEOUT = (5, 90)


@dataclass
class Result:
    ok: bool
    data: Any = None
    message: str = ""


class BackendClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"} if token else {}

    # ---------------------------------------------------------
    # Common HTTP Request
    # ---------------------------------------------------------
    def _request(self, method, path, token=None, **kwargs):
        headers = kwargs.pop("headers", {}).copy()

        headers.setdefault("Accept", "application/json")

        # Add JWT authentication
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.request(
                method,
                self.base_url + path,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

        except requests.Timeout:
            return Result(
                False,
                None,
                "The FastAPI backend did not respond before the request timed out.",
            )
        except requests.RequestException as exc:
            return Result(
                False,
                None,
                f"Cannot connect to FastAPI backend: {exc}",
            )

        # Try to read JSON response
        try:
            data = response.json()
        except ValueError:
            data = response.text

        # Successful response
        if response.ok:
            return Result(
                True,
                data,
                "",
            )

        # Error response
        if isinstance(data, dict):
            detail = data.get("detail") or data.get("message") or str(data)
        else:
            detail = str(data)

        return Result(
            False,
            data,
            f"{response.status_code}: {detail}",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------
    def register(self, email, password):
        return self._request(
            "POST",
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

    def login(self, email, password):
        return self._request(
            "POST",
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    def logout(self, token):
        return self._request("POST", "/api/auth/logout", token=token)

    # ---------------------------------------------------------
    # Goals
    # ---------------------------------------------------------
    def get_goals(self, token=None):
        return self._request(
            "GET",
            "/api/goals",
            token=token,
        )

    def get_goal(self, goal_id, token=None):
        return self._request(
            "GET",
            f"/api/goals/{goal_id}",
            token=token,
        )

    def create_goal(self, payload, token=None):
        return self._request(
            "POST",
            "/api/goals",
            token=token,
            json=payload,
        )

    def update_goal(self, goal_id, payload, token=None):
        return self._request(
            "PUT",
            f"/api/goals/{goal_id}",
            token=token,
            json=payload,
        )

    def delete_goal(self, goal_id, token=None):
        return self._request(
            "DELETE",
            f"/api/goals/{goal_id}",
            token=token,
        )

    # ---------------------------------------------------------
    # Analysis
    # ---------------------------------------------------------
    def start_analysis(self, goal_id, token=None):
        return self._request(
            "POST",
            f"/api/analysis/{goal_id}",
            token=token,
        )

    def get_analysis(self, analysis_id, token=None):
        return self._request(
            "GET",
            f"/api/analysis/{analysis_id}",
            token=token,
        )

    # ---------------------------------------------------------
    # Market
    # ---------------------------------------------------------
    def market(self, symbol, token=None):
        return self._request(
            "GET",
            f"/api/market/{symbol}",
            token=token,
        )

    # ---------------------------------------------------------
    # What-If Analysis
    # ---------------------------------------------------------
    def what_if(
        self,
        goal_id,
        monthly_contribution,
        horizon_years,
        token=None,
    ):
        return self._request(
            "POST",
            "/api/what-if",
            token=token,
            json={
                "goal_id": goal_id,
                "monthly_contribution": monthly_contribution,
                "horizon_years": horizon_years,
            },
        )

    # ---------------------------------------------------------
    # AI Chat
    # ---------------------------------------------------------
    def chat(self, goal_id, message, token=None):
        return self._request(
            "POST",
            "/api/chat",
            token=token,
            json={
                "goal_id": goal_id,
                "message": message,
            },
        )

    # ---------------------------------------------------------
    # Optional POST
    # ---------------------------------------------------------
    def optional_post(self, path, payload, token=None):
        return self._request(
            "POST",
            path,
            token=token,
            json=payload,
        )
    def get_profile(self, token=None):
        return self._request(
            "GET",
            "/api/profile",
            token=token,
    )


    def save_profile(self, payload, token=None):
        return self._request(
            "POST",
            "/api/profile",
            token=token,
            json=payload,
        )

    def get_risk(self, token=None):
        return self._request(
            "GET",
            "/api/risk",
            token=token,
        )
