from python_logging.logger import logger
from batched_queue import BatchedQueue
from web_request import aiohttp_fetch, playwright_fetch
from exceptions import InvalidResponseType

from playwright.async_api import async_playwright
from urllib.parse import urlparse
from collections import defaultdict
from bs4 import BeautifulSoup, element

import concurrent.futures
import asyncio
import aiohttp
import copy

logger.config(file="webscraper.log", ptt=True, clear_log=True, colours=True)


def run_scraping_session(
        urls: list[str] = None, 
        batch_size: int = 8,
        scraping_data: dict = None,
        aiohttp_urls: bool = False,
        playwright_urls: bool = False
    ) -> list:

    try:

        urls = process_urls(urls)
        queue = BatchedQueue(urls, batch_size, scraping_data, aiohttp_urls, playwright_urls)

        return asyncio.run(process_batches(queue))

    except:
        pass


def process_urls(urls: list) -> list:
    """
    Orders a list of urls such that the urls from the same website are as far apart as possible. 
    For example if you have 6 urls from 3 different websites, the list will be order as below:
    - website1, website2, website3, website1, website2, website3

    Args:
        urls (list): A list of URLs to be ordered.

    Returns:
        list: The ordered list of URLs/
    """
    try:

        # Create a dictionary to group URLs by domain
        url_groups = defaultdict(list)

        for url in urls:
            domain = url.split('/')[2]  # Extracting domain from the URL
            url_groups[domain].append(url)
        
        # Sort the groups based on the count of URLs in each group
        sorted_groups = sorted(url_groups.values(), key=len, reverse=True)
        
        # Interleave the groups to form the ordered list
        ordered_urls = [url for i in range(max(map(len, sorted_groups))) for group in sorted_groups for url in group[i:i+1]]

        return ordered_urls

    except:
        pass


async def process_batches(queue: BatchedQueue, batch_delay_seconds=10):
    """
    This function is designed to be an asynchronous task that continuously pops batches of URLs
    from the provided BatchedQueue and sends requests to the urls asynchronously using aiohttp.
    A delay is introduced between each batch processing cycle to control the rate of URL processing.
    The responses from asynchronous requests are then handed off to a ThreadPoolExecutor for
    parallelized CPU-bound scraping tasks, performed by the 'scrape' function.

    Args:
        queue (BatchedQueue): An instance of BatchedQueue containing URLs to be processed.
        batch_delay_seconds (int, optional): The delay in seconds between processing batches. Default is 10 seconds.

    Returns:
        List: A list containing the results collected by the 'scrape' function for each processed batch.
    """
    results = {}
    try:

        # Continuously process batches until the queue is empty
        while queue.length > 0:
            
            batch_urls = queue.pop()

            if queue.aiohttp_urls:
                # If the urls in the queue need to be requested using aiohttp then run
                # the function 'aiohttp_request'
                responses = await aiohttp_request(batch_urls)
            elif queue.playwright_urls:
                # If the urls in the queue need to be requested using playwright then run
                # the function 'playwright_request'
                responses = await playwright_request(batch_urls, queue)
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Use ThreadPoolExecutor to parallelize the CPU-bound scraping task
                batch_results = list(executor.map(lambda args: scrape(queue.scraping_data, *args), zip(responses, batch_urls)))

            for url in batch_urls:
                # Collect the results for each url in the batch_results
                website_name = get_website_name(url)
                results[website_name] = []
                for result_website_name, result in [result for result in batch_results if result is not None]:
                    if website_name == result_website_name:
                        # Match the current url to the batch_result url
                        # and then append the result to results
                        results[website_name].append(result)

            await asyncio.sleep(batch_delay_seconds)

        return results

    except Exception as error:
        # Handle the exception or log the error
        logger.error("Error", error=error)

    return results


async def aiohttp_request(batch_urls: list):
    """
    Create an aiohttp session and send requests asynchronously to each url
    """
    async with aiohttp.ClientSession() as session:
        tasks = [aiohttp_fetch(url, session) for url in batch_urls]
        # Use asyncio.gather to wait for all asynchronous requests to complete
        return await asyncio.gather(*tasks)
    

async def playwright_request(batch_urls: list, queue: BatchedQueue):
    """
    Create a playwright session and create a browser and context
    Create a page for each url and get that page to send a request to the url

    Args: 
        batch_urls (list): A list of urls from the current batch
        queue: (BatchedQueue): An instance of BatchedQueue containing URLs to be processed. 
    
    Returns:
        List: A list of responses collected from each request
    """
    try:
        # Initialise playwright
        async with async_playwright() as playwright:
            # Open a browser
            browser = await playwright.firefox.launch()
            # Create a browser context
            context = await browser.new_context()
            try:

                tasks = [
                    playwright_fetch(
                        url,                                                 # url
                        await context.new_page(),                            # page
                        queue.scraping_data[get_website_name(url)]["xpath"]  # xpath
                    ) for url in batch_urls
                ]

                # Use asyncio.gather to wait for all asynchronous requests to complete
                batch_results = await asyncio.gather(*tasks)

                for page in context.pages:
                    await page.close()

            finally:
                # Close the browser, context, and pages
                for page in context.pages:
                    await page.close()

                await context.close()
                await browser.close()

            return batch_results

    except Exception as error:
        logger.error(f"Unhandled error when creating playwright instance", error=error)


def scrape(scraping_data: dict, *args: tuple):
    try:

        response, url = args
        if isinstance(response, int):
            # This is the response code
            return (response, url)
        
        website_name = get_website_name(url)

        scraped_data = {}

        response_type = scraping_data[website_name].get("type")

        # If the response is in html then scrape the data using the html function
        if response_type == "html":
            html = BeautifulSoup(response, "lxml")
            tag_info = scraping_data[website_name]["data"]

            for item_name, item_info in tag_info.items():
                scraped_data[item_name.replace("multiple ", "")] = scrape_html(html, item_name, item_info)
        
        elif response_type == "json":
            pass

        elif response_type == "xml":
            pass

        else:
            raise InvalidResponseType(response_type, website_name)
        
        return website_name, scraped_data
    
    except Exception as error:
        # Handle the exception or log the error
        logger.error("Error", error=error)


def scrape_html(html: BeautifulSoup, item_name: str, scraping_data: dict) -> dict:
    try:
        # This is the dictionary to hold the scraped data
        scraped_data = {}
        # Get the scraping information for this item
        item_data = scraping_data.get("item-data")
        # Delete the item data from the scraping info as we don't need it in here
        del scraping_data["item-data"]
        
        for tag_info in item_data:
            # To find the tag there might be multiple things to scrape 
            # Each tag_info is a tag to scrape for. The last item in item data
            # is what the final html will be set to
            html, multiple = scrape_html_tag(html, tag_info)

        if multiple is True:
            # Scrape for multiple tags
            scraped_data = handle_multiple_html_tags(html, scraping_data)
        else:
            # Scrape for a single tag
            scraped_data = handle_single_html_tag(html, scraping_data, tag_info)

        return scraped_data
    
    except Exception as error:
        # Handle the exception or log the error
        logger.error("Error", error=error)
        return None


def handle_multiple_html_tags(html, scraping_data: dict):
    try:
        # This is the list that will contain the items found in the tags
        scraped_data = []

        for tag in html:
            # Loop through each tag that was found in the html
            # This is the dictionary that contains the current tag information
            tag_data = {}
            # Make a deep copy of the scraping data each loop as it gets modified
            scraping_data_copy = copy.deepcopy(scraping_data)
            
            for item_name, item_data in scraping_data_copy.items():
                # Loop through the scraping data for each item to be scraped in the tag
                # Run the scrape_html function to scrape the data for this item in the tag
                tag_data[item_name] = scrape_html(tag, item_name, item_data)
            
            scraped_data.append(tag_data)

        return scraped_data
    
    except:
        pass


def handle_single_html_tag(html: BeautifulSoup, scraping_data: dict, tag_info: dict):
    try:
        scraped_data = {}

        attribute = tag_info.get("attr", None)

        if attribute is None:
            # If attribute is None, then we will scrape for more data
            scraping_data_copy = copy.deepcopy(scraping_data)
            for item_name, item_data in scraping_data_copy.items():
                scraped_data[item_name] = scrape_html(html, item_name, item_data)

        elif attribute == ".text":
            scraped_data = html.text

        else:
            scraped_data = html[attribute]
        
        return scraped_data
    
    except:
        pass


def scrape_html_tag(html: BeautifulSoup, tag_info: dict) -> tuple[BeautifulSoup, bool]:
    try:
        # Get the html for the item
        tag = tag_info["tag"]
        attr_name, attr_value = list(tag_info.items())[1]
        attrs = {attr_name: attr_value}

        # Get the number of tags to scrape for
        num_items = tag_info.get("max", None)
        
        if num_items is None:
            # Scrape for only a single item
            return (html.find(name=tag, attrs=attrs), False)
            
        else:
            # Scrape for multiple items
            return (html.find_all(name=tag, attrs=attrs)[:num_items], True)

    except:
        pass


def get_website_name(url: str) -> str:
    """
    Extracts the website name from a url
    """

    domain = urlparse(url).netloc
    # Split the domain into subdomains and domain parts
    _, _, main_domain = domain.partition('.')
    # Split the main domain into parts based on dots
    domain_parts = main_domain.split('.')
    return domain_parts[0]