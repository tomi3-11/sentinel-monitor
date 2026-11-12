import socket
import ssl
from datetime import UTC, datetime
from urllib.parse import urlparse


def get_ssl_expiry_days(url: str, timeout: int = 5) -> int | str:
    """
    Connect to a given URL over port 443, extracts the SSL certificate,
    and calculates the number of days until it expires.
    """
    try:
        # Parse the hostname from the URL (e.g., https://google.com -> google.com)
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        # If the site doesn't use HTTPS, we bypass the check
        if parsed_url.scheme != "https":
            return "Not HTTPS"

        if not hostname:
            return "Invalid HTTPS URL"

        # Create a standard network socket and an SSL context
        context = ssl.create_default_context()
        with (
            socket.create_connection((hostname, 443), timeout=timeout) as sock,
            context.wrap_socket(sock, server_hostname=hostname) as ssock,
        ):
            # Request the server's certificate
            cert = ssock.getpeercert()

            # The 'notAfter' date is formatted like: 'Apr 23 23:59:59 2026 GMT'
            expire_date_str = cert["notAfter"]

            # Convert the string into UTC datetime object
            expire_date = datetime.strptime(expire_date_str, "%b %d %H:%M:%S %Y %Z")
            expire_date = expire_date.replace(tzinfo=UTC)

            # Calculate the days remaining
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
    # Testing a known good site and a bad/non-existent site
    test_urls = [
        "https://google.com",
        "http://neverssl.com",
        "https://this-does-not-exist.org",
    ]

    for test_url in test_urls:
        days_left = get_ssl_expiry_days(test_url)
        print(f"[{test_url}] SSL Days Remaining: {days_left}")
