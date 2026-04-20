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


def test_get_company_success(mock_transport, load_fixture):
    fixture = load_fixture("company_sas.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/companies/732829320"
        assert request.headers["Authorization"] == "Bearer jwt-abc"
        return httpx.Response(200, json=fixture)

    client = Client(token="jwt-abc", transport=mock_transport(handler))
    data = client.get_company("732829320")
    assert data["siren"] == "732829320"


def test_get_company_not_found(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not found"})

    client = Client(token="jwt-abc", transport=mock_transport(handler))
    with pytest.raises(RNENotFoundError, match="SIREN"):
        client.get_company("999999999")


def test_get_company_unauthorised(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid token"})

    client = Client(token="expired", transport=mock_transport(handler))
    with pytest.raises(RNEAuthError, match="rne login"):
        client.get_company("732829320")


def test_get_company_no_token():
    client = Client(token=None)
    with pytest.raises(RNEAuthError, match="rne login"):
        client.get_company("732829320")
