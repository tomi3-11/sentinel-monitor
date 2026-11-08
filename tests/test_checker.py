import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monitor.checker import SiteResult, check_uptime, run_all_checks
from monitor.config import SiteConfig


@pytest.fixture
def site():
    return SiteConfig(name="Test Site", url="https://example.com")


@pytest.mark.asyncio
async def test_site_is_up(site):
    """A 200 response marks the site is up."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.head.return_value = mock_response

    with patch("monitor.checker.get_ssl_expiry_days", return_value=60):
        result = await check_uptime(mock_client, site)

    assert result.is_up is True
    assert result.status_code == 200
    assert result.name == "Test Site"
    assert result.url == "https://example.com"
    assert result.ssl_days_left == 60
    assert result.error_msg == ""


@pytest.mark.asyncio
async def test_site_is_down(site):
    """A 4xx response marks the site as down."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.head.return_value = mock_response

    with patch("monitor.checker.get_ssl_expiry_days", return_value=60):
        result = await check_uptime(mock_client, site)

    assert result.is_up is False
    assert result.status_code == 404
    assert result.error_msg == ""


@pytest.mark.asyncio
async def test_request_error(site):
    """A network error marks the site as down with an error message."""
    import httpx

    mock_client = AsyncMock()
    mock_client.head.side_effect = httpx.RequestError("DNS resolution failed")

    with patch("monitor.checker.get_ssl_expiry_days", return_value="DNS Lookup Failed"):
        result = await check_uptime(mock_client, site)

    assert result.is_up is False
    assert result.status_code == 0
    assert "DNS resolution failed" in result.error_msg
    assert result.ssl_days_left == "DNS Lookup Failed"


@pytest.mark.asyncio
async def test_http_and_ssl_checks_overlap(site):
    """The SSL worker must start before the HTTP probe is allowed to finish."""
    ssl_started = threading.Event()
    release_ssl = threading.Event()

    def inspect_ssl(_url):
        ssl_started.set()
        release_ssl.wait(timeout=2)
        return 45

    async def respond_after_ssl_starts(*_args, **_kwargs):
        started = await asyncio.to_thread(ssl_started.wait, timeout=1)
        release_ssl.set()
        assert started, "SSL inspection did not start while the HTTP request was pending"
        response = MagicMock()
        response.status_code = 200
        return response

    mock_client = AsyncMock()
    mock_client.head.side_effect = respond_after_ssl_starts

    try:
        with patch("monitor.checker.get_ssl_expiry_days", side_effect=inspect_ssl):
            result = await check_uptime(mock_client, site)
    finally:
        release_ssl.set()

    assert result.is_up is True
    assert result.ssl_days_left == 45


@pytest.mark.asyncio
async def test_ssl_failure_does_not_discard_http_result(site):
    """An SSL worker exception must not turn a successful HTTP probe into failure."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.head.return_value = mock_response

    with patch(
        "monitor.checker.get_ssl_expiry_days",
        side_effect=RuntimeError("unexpected TLS inspection error"),
    ):
        result = await check_uptime(mock_client, site)

    assert result.is_up is True
    assert result.status_code == 200
    assert result.ssl_days_left.startswith("SSL check failed:")
    assert "unexpected TLS inspection error" in result.ssl_days_left


@pytest.mark.asyncio
async def test_run_all_checks_returns_all_results():
    """All sites are checked and results returned for each."""
    sites = [
        SiteConfig(name="Site One", url="https://one.example.com"),
        SiteConfig(name="Site Two", url="https://two.example.com"),
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200

    with (
        patch("monitor.checker.get_ssl_expiry_days", return_value=90),
        patch(
            "httpx.AsyncClient.head",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
    ):
        results = await run_all_checks(sites, timeout=5)

    assert len(results) == 2
    assert all(isinstance(r, SiteResult) for r in results)
    assert all(r.is_up for r in results)
