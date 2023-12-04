from python_logging.logger import logger
from fake_headers import Headers

import playwright


# Request limitations
BLOCKED_RESOURCE_TYPES = ["stylesheet", "font", "media", "other", "ico", "svg", "css", "json", "xml"]
PLAYWRIGHT_PAGE_TIMEOUT = 30000


async def aiohttp_fetch(url, session) -> None:
    async with session.get(url, headers=headers()) as response:
        status = response.status
        if await check_response_status(status, url):
            return await response.text()
        return status


async def playwright_fetch(url, page, xpath):
    """
    Uses playwright to open up a webpage and get the html
    """
    try:
        # Remove all unnecessary content from the request 
        await page.route("**/*", intercept_request)
        # Set timeout
        page.set_default_navigation_timeout(PLAYWRIGHT_PAGE_TIMEOUT)
        # Add headers to request
        await page.set_extra_http_headers(headers())
        # Make request
        response = await page.goto(url)

        # Check the HTTP status code
        status = response.status

        # Use the check_response_status function
        response_check = await check_response_status(status, url)

        if response_check is True:
            # If everything goes well, return the content as a BeautifulSoup object
            locator = page.locator(xpath)
            return await locator.first.inner_html()
            
        else:
            # If it's not a good response, return the check result
            return response_check

    except playwright.async_api.TimeoutError:
        pass

    except Exception as error:
        if str(error) == "Connection closed while reading from the driver":
            return
        logger.error(msg="Unmanaged error in (get_html_by_playwright)", error=error)


async def intercept_request(route, request):
    if request.resource_type in BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()


def headers():
    """
    Generate random headers
    """
    header = Headers(headers=True)

    return header.generate()


async def check_response_status(status_code, url):
    if status_code in [302, 303, 500, 502, 503]:
        # These status codes are due to the server not the request
        return None

    elif status_code in [301, 308, 400, 404, 410]:
        # These status codes indicate the resource has been moved or there was a bad request
        return None
    
    elif status_code in [403]:
        # 403 is a forbidden error
        logger.warning(f"({url}), Response Status Code {str(status_code)}")
        return None

    elif status_code != 200:
        # Any other error should be logged so it can be handled in the future
        logger.warning(f"({url}), Response Status Code {str(status_code)}")
        return None
    
    else:
        return True