import socket
import ssl
from unittest.mock import MagicMock, patch

from monitor.ssl_utils import get_ssl_expiry_days


def test_non_https_url():
    """HTTP URLs should return 'NOT HTTPS' without making a connection."""
    result = get_ssl_expiry_days("http://example.com")
    assert result == "Not HTTPS"


def test_valid_ssl_cert():
    """Valid HTTPS site returns number of days left as int."""
    mock_cert = {"notAfter": "Jan 01 00:00:00 2030 GMT"}
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = mock_cert

    mock_sock = MagicMock()
    mock_context = MagicMock()
    mock_context.wrap_socket.return_value.__enter__ = MagicMock(return_value=mock_ssock)
    mock_context.wrap_socket.return_value.__exit__ = MagicMock(return_value=False)

    with patch("monitor.ssl_utils.ssl.create_default_context", return_value=mock_context), \
            patch("monitor.ssl_utils.socket.create_connection", return_value=mock_sock):
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        result = get_ssl_expiry_days("https://example.com")

    assert isinstance(result, int)
    assert result > 0


def test_dns_lookup_failure():
    """DNS failure returns descriptive string."""
    with patch("monitor.ssl_utils.socket.create_connection", side_effect=socket.gaierror):
        result = get_ssl_expiry_days("https://this-does-not-exist.example.com")

    assert result == "DNS Lookup Failed"


def test_connection_timeout():
    """Connection timeout returns descriptive string."""
    with patch("monitor.ssl_utils.socket.create_connection", side_effect=socket.timeout):
        result = get_ssl_expiry_days("https://example.com")

    assert result == "Connection Time Out"


def test_ssl_error():
    """SSL handshake failure returns descriptive string."""
    with patch("monitor.ssl_utils.socket.create_connection", side_effect=ssl.SSLError("handshake failed")):
        result = get_ssl_expiry_days("https://example.com")

    assert "SSL Handshake Failed" in result


