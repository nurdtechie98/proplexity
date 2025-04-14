import modal
from typing import List
from pydantic import BaseModel
import os

app = modal.App("website-refresh")

# Create web image with required dependencies
web_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "requests", "pydantic"
)


class RefreshResponse(BaseModel):
    jobs_started: List[str]
    websites_refreshed: List[str]


@app.function(
    image=web_image,
    secrets=[modal.Secret.from_name("api-credentials")],
    schedule=modal.Period(days=1),
)
async def refresh_stale_websites() -> RefreshResponse:
    """Check for and refresh stale websites via API calls.

    This function runs daily and performs the following steps:
    1. Retrieves list of stale websites from the API
    2. For each stale website:
        - Starts a new spider job
        - Updates the website's last_scraped timestamp
        - Tracks job IDs and refreshed URLs
    3. Returns summary of operations performed

    Environment Requirements:
        - API_BASE_URL: Base URL for the API endpoints
        - API_KEY: Authentication key for API access

    Returns:
        RefreshResponse: Object containing:
            - jobs_started: List of started job IDs
            - websites_refreshed: List of processed URLs

    Raises:
        Exceptions are caught and logged, returning empty lists in case of
        errors
    """
    import requests

    api_base_url = os.environ["API_BASE_URL"]
    api_key = os.environ["API_KEY"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Get stale websites from API
        response = requests.get(
            f"{api_base_url}/websites/stale",
            headers=headers
        )
        response.raise_for_status()
        stale_websites = response.json()

        jobs_started = []
        websites_refreshed = []

        # Process each stale website
        for website in stale_websites:
            try:
                # Start spider job
                spider_response = requests.post(
                    f"{api_base_url}/scraper/spider/start",
                    headers=headers,
                    json={
                        "start_url": website["url"],
                        "max_urls": website["max_urls"]
                    },
                )
                spider_response.raise_for_status()
                job_data = spider_response.json()

                # Update website's last_scraped timestamp via API
                update_response = requests.put(
                    f"{api_base_url}/websites/{website['id']}/refresh",
                    headers=headers
                )
                update_response.raise_for_status()

                jobs_started.append(job_data["job_id"])
                websites_refreshed.append(website["url"])

                print(f"Started refresh job {job_data['job_id']} for {website['url']}")

            except Exception as e:
                print(f"Error refreshing {website['url']}: {str(e)}")
                continue

        return RefreshResponse(
            jobs_started=jobs_started, websites_refreshed=websites_refreshed
        )

    except Exception as e:
        print(f"Error in refresh process: {str(e)}")
        return RefreshResponse(jobs_started=[], websites_refreshed=[])
