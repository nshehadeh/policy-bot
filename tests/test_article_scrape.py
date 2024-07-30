import requests
from bs4 import BeautifulSoup
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from whgov_scraper import scrape_article



# List of example article URLs to test the scraper
test_urls = [
    'https://www.whitehouse.gov/briefing-room/blog/2024/07/01/building-a-thriving-clean-energy-economy-in-2023-and-beyond-a-six-month-update/',
    'https://www.whitehouse.gov/briefing-room/statements-releases/2024/07/01/readout-of-principal-deputy-national-security-advisor-jon-finers-meeting-with-prime-minister-garry-conille-of-haiti/',
    'https://www.whitehouse.gov/briefing-room/press-briefings/2024/06/20/on-the-record-press-gaggle-by-white-house-national-security-communications-advisor-john-kirby-15/'
]
def test_scrape_article():
    for url in test_urls:
        try:
            article_details = scrape_article(url)
            print("Article details:")
            for key, value in article_details.items():
                if key != 'content':
                    print(f"{key}: {value}")
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error scraping article at {url}: {e}")

if __name__ == "__main__":
    test_scrape_article()