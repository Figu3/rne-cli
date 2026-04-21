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


def test_search_single_page(mock_transport, load_fixture):
    fixture = load_fixture("search_results.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/companies"
        assert request.url.params["companyName"] == "danone"
        return httpx.Response(200, json=fixture)

    client = Client(token="jwt", transport=mock_transport(handler))
    results = client.search("danone", limit=20)
    assert len(results) == 2


def test_search_paginates_until_limit(mock_transport):
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        page = int(request.url.params["page"])
        if page <= 3:
            items = [{"siren": f"{page:03d}{i:06d}"} for i in range(20)]
        else:
            items = []
        return httpx.Response(200, json=items)

    client = Client(token="jwt", transport=mock_transport(handler))
    results = client.search("big", limit=50)
    assert len(results) == 50
    assert call_count["n"] >= 2


def test_search_stops_on_empty_page(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        if page == 1:
            return httpx.Response(200, json=[{"siren": "111111111"}])
        return httpx.Response(200, json=[])

    client = Client(token="jwt", transport=mock_transport(handler))
    results = client.search("rare", limit=100)
    assert len(results) == 1


def test_search_limit_zero_rejected():
    client = Client(token="jwt")
    with pytest.raises(RNEValidationError, match="limit"):
        client.search("x", limit=0)


def test_get_attachments(mock_transport, load_fixture):
    fixture = load_fixture("attachments.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/companies/732829320/attachments"
        return httpx.Response(200, json=fixture)

    client = Client(token="jwt", transport=mock_transport(handler))
    data = client.get_attachments("732829320")
    assert "bilans" in data
    assert "actes" in data
    assert len(data["bilans"]) == 1


def test_get_history(mock_transport):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/companies/diff"
        assert request.url.params["siren[]"] == "732829320"
        assert request.url.params["from"] == "2024-01-01"
        assert request.url.params["to"] == "2024-12-31"
        return httpx.Response(200, json=[
            {"siren": "732829320", "submitDate": "2024-03-15", "change": "denomination"}
        ])

    client = Client(token="jwt", transport=mock_transport(handler))
    changes = client.get_history("732829320", date_from="2024-01-01", date_to="2024-12-31")
    assert len(changes) == 1


def test_cache_hit_avoids_second_call(mock_transport, fake_home, load_fixture):
    fixture = load_fixture("company_sas.json")
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json=fixture)

    c = Client(token="jwt", transport=mock_transport(handler), use_cache=True)
    c.get_company("732829320")
    c.get_company("732829320")
    assert call_count["n"] == 1  # second call was served from cache


def test_no_cache_flag_refetches(mock_transport, fake_home, load_fixture):
    fixture = load_fixture("company_sas.json")
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json=fixture)

    c = Client(token="jwt", transport=mock_transport(handler), use_cache=False)
    c.get_company("732829320")
    c.get_company("732829320")
    assert call_count["n"] == 2


def test_login_connect_error_friendly_message(mock_transport):
    from rne_cli.errors import RNENetworkError

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("DNS failure", request=request)

    client = Client(transport=mock_transport(handler))
    with pytest.raises(RNENetworkError, match="connexion réseau"):
        client.login("x@y", "pw")
