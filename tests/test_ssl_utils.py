import socket
import ssl
from unittest.mock import MagicMock, patch

import pytest

from monitor.ssl_utils import get_ssl_expiry_days


def test_non_https_url():
    """HTTP URLs should bypass SSL inspection without making a connection."""
    with patch("monitor.ssl_utils.socket.create_connection") as create_connection:
        result = get_ssl_expiry_days("http://example.com")

    assert result == "Not HTTPS"
    create_connection.assert_not_called()


@pytest.mark.parametrize(
    ("url", "expected_port"),
    [
        ("https://example.com:8443", 8443),
        ("https://example.com:9443", 9443),
        ("https://example.com", 443),
    ],
)
def test_ssl_inspection_uses_url_port(url, expected_port):
    """SSL inspection should use an explicit HTTPS port or default to 443."""
    mock_cert = {"notAfter": "Jan 01 00:00:00 2030 GMT"}
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = mock_cert

    mock_sock = MagicMock()
    mock_context = MagicMock()
    mock_context.wrap_socket.return_value.__enter__ = MagicMock(return_value=mock_ssock)
    mock_context.wrap_socket.return_value.__exit__ = MagicMock(return_value=False)

    with (
        patch("monitor.ssl_utils.ssl.create_default_context", return_value=mock_context),
        patch("monitor.ssl_utils.socket.create_connection", return_value=mock_sock) as create_connection,
    ):
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        result = get_ssl_expiry_days(url)

    assert isinstance(result, int)
    assert result > 0
    create_connection.assert_called_once_with(("example.com", expected_port), timeout=5)
    mock_context.wrap_socket.assert_called_once_with(mock_sock, server_hostname="example.com")


def test_invalid_https_port_returns_error():
    """Malformed ports should return a useful error rather than raising."""
    result = get_ssl_expiry_days("https://example.com:invalid")

    assert isinstance(result, str)
    assert result.startswith("Error:")


def test_dns_lookup_failure():
    """DNS failure returns a descriptive string."""
    with patch("monitor.ssl_utils.socket.create_connection", side_effect=socket.gaierror):
        result = get_ssl_expiry_days("https://this-does-not-exist.example.com")

    assert result == "DNS Lookup Failed"


def test_connection_timeout():
    """Connection timeout returns a descriptive string."""
    with patch("monitor.ssl_utils.socket.create_connection", side_effect=socket.timeout):
        result = get_ssl_expiry_days("https://example.com")

    assert result == "Connection Time Out"


def test_ssl_error():
    """SSL handshake failure returns a descriptive string."""
    with patch(
        "monitor.ssl_utils.socket.create_connection",
        side_effect=ssl.SSLError("handshake failed"),
    ):
        result = get_ssl_expiry_days("https://example.com")

    assert "SSL Handshake Failed" in result
