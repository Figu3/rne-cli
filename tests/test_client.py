import httpx
import pytest

from rne_cli.client import Client
from rne_cli.errors import RNEAuthError, RNENotFoundError, RNEValidationError


def test_login_success(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/sso/login"
        assert request.method == "POST"
        body = request.content.decode()
        assert '"username"' in body and '"password"' in body
        return httpx.Response(200, json={"token": "jwt-abc-123"})

    client = Client(transport=mock_transport(handler))
    token = client.login("me@example.com", "pw")
    assert token == "jwt-abc-123"


def test_login_bad_credentials(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid credentials"})

    client = Client(transport=mock_transport(handler))
    with pytest.raises(RNEAuthError, match="identifiants"):
        client.login("me@example.com", "wrong")
