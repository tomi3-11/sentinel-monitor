import asyncio
import httpx
import time
from dataclasses import dataclass
from typing import List
from monitor.config import SiteConfig, load_config
from monitor.ssl_utils import get_ssl_expiry_days


@dataclass
class SiteResult:
    """Stores the result of a single website check."""

    name: str
    url: str
    is_up: bool
    status_code: int
    response_time_ms: float
    ssl_days_left: int | str
    error_msg: str = ""


async def _probe_http(
    client: httpx.AsyncClient, site: SiteConfig
) -> tuple[httpx.Response | None, float, httpx.RequestError | None]:
    """Run the HTTP probe and retain its own response time and request error."""
    start_time = time.perf_counter()

    try:
        response = await client.head(site.url, follow_redirects=True)
    except httpx.RequestError as error:
        elapsed = (time.perf_counter() - start_time) * 1000
        return None, round(elapsed, 2), error

    elapsed = (time.perf_counter() - start_time) * 1000
    return response, round(elapsed, 2), None


async def check_uptime(client: httpx.AsyncClient, site: SiteConfig) -> SiteResult:
    """
    Check HTTP reachability and SSL expiry concurrently for one site.

    Each result is collected independently so an SSL inspection failure does
    not discard a successful HTTP response, and an HTTP request failure does
    not discard the SSL inspection result.
    """
    http_task = asyncio.create_task(_probe_http(client, site))
    ssl_task = asyncio.create_task(asyncio.to_thread(get_ssl_expiry_days, site.url))

    try:
        http_result, ssl_result = await asyncio.gather(
            http_task, ssl_task, return_exceptions=True
        )
    except asyncio.CancelledError:
        # Cancel pending asyncio work before propagating caller cancellation.
        http_task.cancel()
        ssl_task.cancel()
        await asyncio.gather(http_task, ssl_task, return_exceptions=True)
        raise

    # A task cancelled independently should still cancel the site check.
    if isinstance(http_result, asyncio.CancelledError):
        raise http_result
    if isinstance(ssl_result, asyncio.CancelledError):
        raise ssl_result

    # Unexpected HTTP failures should not be misreported as ordinary outages.
    if isinstance(http_result, BaseException):
        raise http_result

    response, elapsed, request_error = http_result

    # SSL inspection is best-effort and independent from HTTP reachability.
    if isinstance(ssl_result, Exception):
        ssl_days: int | str = f"SSL check failed: {ssl_result}"
    elif isinstance(ssl_result, BaseException):
        raise ssl_result
    else:
        ssl_days = ssl_result

    if request_error is not None:
        return SiteResult(
            name=site.name,
            url=site.url,
            is_up=False,
            status_code=0,
            response_time_ms=elapsed,
            error_msg=str(request_error),
            ssl_days_left=ssl_days,
        )

    return SiteResult(
        name=site.name,
        url=site.url,
        is_up=response.status_code < 400,
        status_code=response.status_code,
        response_time_ms=elapsed,
        ssl_days_left=ssl_days,
    )


async def run_all_checks(sites: List[SiteConfig], timeout: int) -> List[SiteResult]:
    """
    Takes a list of sites and checks them all concurrently using an event loop.
    """

    async with httpx.AsyncClient(timeout=timeout) as client:
        # We open ONE connection pool to be shared across all requests
        tasks = [check_uptime(client, site) for site in sites]
        # asyncio.gather fires all tasks at exactly the same time
        return await asyncio.gather(*tasks)


# Quick Test
if __name__ == "__main__":
    # Using try and except since it is being run directly for testing
    try:
        app_config = load_config("../targets.yaml")
    except FileNotFoundError:
        app_config = load_config("targets.yaml")

    print(f"Starting concurrent checks for {len(app_config.sites)} sites...\n")

    # Run the asynchronous event loop
    start_total = time.perf_counter()
    results = asyncio.run(run_all_checks(app_config.sites, app_config.timeout))
    total_time = time.perf_counter() - start_total

    # Print the result
    for res in results:
        status = "UP" if res.is_up else "DOWN"
        print(
            f"{status} | {res.status_code} | {res.response_time_ms}ms | {res.name} ({res.url})"
        )
        if res.error_msg:
            print(f"    Error: {res.error_msg}")

    print(f"\nTotal execution time for all sites: {total_time:.2f} seconds")
