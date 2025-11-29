from playwright.sync_api import sync_playwright
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import yfinance
import requests
import asyncio
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize MCP Server
mcp_server = FastMCP(name="AmazonPriceTracker")


def get_product_by_name(search_url, product_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    }
    resp = requests.get(search_url, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch page, status: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.find_all("div", {"data-component-type": "s-search-result"})

    for item in results:
        # To get the product title
        title_tag = item.h2
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        if product_name.lower() in title.lower():
            # To fetch price
            price_whole = item.select_one("span.a-price-whole")
            price_fraction = item.select_one("span.a-price-fraction")
            if not price_whole:
                continue

            price = price_whole.get_text(strip=True)
            if price_fraction:
                price += "." + price_fraction.get_text(strip=True)

            # To fetch the product link
            link_tag = item.find("a", {"class": "a-link-normal", "href": True})
            product_url = (
                urljoin("https://www.amazon.in", link_tag["href"]) if link_tag else None
            )

            return {"title": title, "price": price, "url": product_url}

    raise Exception(f"No product found matching '{product_name}'")


@mcp_server.tool(
    name="amazon_scraper", description="Fetch price of the first Amazon product."
)
async def amazon_scraper(input_str: str):
    product_name = input_str
    product_name_for_url = product_name.replace(" ", "+")
    url = f"https://www.amazon.in/s?k={product_name_for_url}"
    product = get_product_by_name(url, product_name)

    return product


if __name__ == "__main__":
    print("MCP [Amazon_Price_Fetcher] server started...")
    mcp_server.run(transport="stdio")
