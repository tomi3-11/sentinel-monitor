import socket
import ssl
from datetime import UTC, datetime
from urllib.parse import urlparse


def get_ssl_expiry_days(url: str, timeout: int = 5) -> int | str:
    """
    Connect to a given HTTPS URL, extract its SSL certificate,
    and calculate the number of days until it expires.
    """
    try:
        parsed_url = urlparse(url)

        # If the site doesn't use HTTPS, we bypass the check.
        if parsed_url.scheme != "https":
            return "Not HTTPS"

        hostname = parsed_url.hostname
        if not hostname:
            return "Invalid HTTPS URL"

        # Use the URL's explicit port, falling back to the HTTPS default.
        parsed_port = parsed_url.port
        port = 443 if parsed_port is None else parsed_port

        context = ssl.create_default_context()
        with (
            socket.create_connection((hostname, port), timeout=timeout) as sock,
            context.wrap_socket(sock, server_hostname=hostname) as ssock,
        ):
            cert = ssock.getpeercert()
            expire_date_str = cert["notAfter"]

            expire_date = datetime.strptime(expire_date_str, "%b %d %H:%M:%S %Y %Z")
            expire_date = expire_date.replace(tzinfo=UTC)

            time_left = expire_date - datetime.now(UTC)
            return time_left.days

    except socket.gaierror:
        return "DNS Lookup Failed"
    except TimeoutError:
        return "Connection Time Out"
    except ssl.SSLError as e:
        return f"SSL Handshake Failed: {e}"
    except (OSError, ValueError, KeyError) as e:
        return f"Error: {e}"


# Quick test
if __name__ == "__main__":
    test_urls = [
        "https://google.com",
        "http://neverssl.com",
        "https://this-does-not-exist.org",
    ]

    for test_url in test_urls:
        days_left = get_ssl_expiry_days(test_url)
        print(f"[{test_url}] SSL Days Remaining: {days_left}")
