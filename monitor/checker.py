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


async def check_uptime(client: httpx.AsyncClient, site: SiteConfig) -> SiteResult:
    """
    Pings a single website asynchronously.
    We use a HEAD request instead of GET to save bandwidth.
    """
    start_time = time.perf_counter()
    ssl_task = asyncio.to_thread(get_ssl_expiry_days, site.url)
    ssl_days = "Pending"
    elapsed = 0.0

    try:
        # A HEAD request asks the server for the headers only, not the full HTML body.
        # This makes the check much faster and less taxing on the target server.
        response = await client.head(site.url, follow_redirects=True)
        elapsed = (time.perf_counter() - start_time) * 1000
        ssl_days = await ssl_task

        return SiteResult(
            name=site.name,
            url=site.url,
            # Treat any 2xx or 3xx status code as "Up"
            is_up=response.status_code < 400,
            status_code=response.status_code,
            response_time_ms=round(elapsed, 2),
            ssl_days_left=ssl_days,
        )
    except httpx.RequestError as e:
        # Catches DNS failures, connection timeouts, etc.
        elapsed = (time.perf_counter() - start_time) * 1000
        ssl_days = await ssl_task

        return SiteResult(
            name=site.name,
            url=site.url,
            is_up=False,
            status_code=0,
            response_time_ms=round(elapsed, 2),
            error_msg=str(e),
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
            f"{status} | {res.status_code} | {res.response_time_ms:.2f}ms | {res.name} ({res.url})"
        )
        if res.error_msg:
            print(f"    Error: {res.error_msg}")

    print(f"\nTotal execution time for all sites: {total_time:.2f} seconds")
