    
import requests
from bs4 import BeautifulSoup
import os
import sys
from pymongo import MongoClient
from pydantic import ValidationError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.etl_pipeline.scrapers.whgov_scraper import scrape_article, WHArticle


# List of example article URLs to test the scraper
test_urls = [
    'https://www.whitehouse.gov/briefing-room/statements-releases/2024/07/01/readout-of-principal-deputy-national-security-advisor-jon-finers-meeting-with-prime-minister-garry-conille-of-haiti/',
]

def test_scrape_article():
    for url in test_urls:
        try:
            article_details = scrape_article(url)
            print("Article details:")
            for key, value in article_details.items():
                if key != 'content':
                    print(f"{key}: {value}")
                else:
                    print(f"Word count: {len(value.split())}")
            print("\n" + "="*80 + "\n")
            
            # Validate article data with Pydantic model
            article = WHArticle(**article_details)
            print("Article is valid.\n")

        except ValidationError as e:
            print(f"Validation error for article at {url}: {e}")


if __name__ == "__main__":
    test_scrape_article()
