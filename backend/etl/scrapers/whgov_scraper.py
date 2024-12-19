"""
White House Briefing Room Scraper

This module scrapes articles from the White House Briefing Room website and stores them in MongoDB.
It handles pagination, concurrent scraping, and data validation using Pydantic models.

Dependencies:
    - MongoDB connection string in environment variables
    - requests for HTTP requests
    - BeautifulSoup4 for HTML parsing
    - Pydantic for data validation
"""

from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from dotenv import load_dotenv
import os
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm
from html import unescape
import re

# Load environment variables and setup MongoDB connection
load_dotenv()
connection_string = os.getenv('MONGO_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['WTP']
collection = db['whbriefingroom']

# Base URL for the White House Briefing Room pages
BASE_URL = 'https://www.whitehouse.gov/briefing-room/page/'

class WHArticle(BaseModel):
    """
    Pydantic model for White House article validation and storage.
    
    Attributes:
        title: Article title
        category: Article category, must be one of the predefined types
        date_posted: Publication date
        content: Article content
        url: Article URL
        source: Source of the article, defaults to White House Gov Briefing Room
    """
    title: str
    # Raises validation error if type is not a category
    category: Literal['Blog', 'Disclosures', 'Legislation', 'Presidential Actions', 'Press Briefings', 'Speeches and Remarks', 'Statements and Releases']
    date_posted: str
    content: str
    url: str
    source: str = Field(default="White House Gov Briefing Room")

def insert_article(article_data):
    """
    Insert or update an article in the MongoDB collection.
    
    Args:
        article_data (dict): Article data matching the WHArticle schema
        
    Note:
        Uses upsert to avoid duplicates based on article URL
    """
    try:
        article = WHArticle(**article_data)
        collection.update_one(
            {"url": article.url},
            {"$set": article.model_dump()},
            upsert=True
        )
    except ValidationError as e:
        print(f"Validation error inserting an article: {e}")    

def fetch_url(url):
    """
    Fetch content from a URL using requests.
    
    Args:
        url (str): URL to fetch
        
    Returns:
        requests.Response: Response object from the request
    """
    response = requests.get(url)
    # No sleep for now, possibly implement this if you're getting errors/ temp bans from website
    # time.sleep(random.uniform(1, 3))
    return response

def parse_page(content):
    """
    Parse article URLs from a briefing room page.
    
    Args:
        content (str): HTML content of the page
        
    Returns:
        list: List of article URLs found on the page
    """
    soup = BeautifulSoup(content, 'html.parser')
    articles = soup.find_all('article', class_='news-item')
    links = []
    for article in articles:
        link = article.find('a', class_='news-item__title')['href']
        links.append(link)
    return links

def scrape_page(page_number):
    """
    Scrape a single page of the briefing room.
    
    Args:
        page_number (int): Page number to scrape
        
    Returns:
        list: List of article URLs found on the page
    """
    url = f"{BASE_URL}{page_number}/"
    response = fetch_url(url)
    if response.status_code == 200:
        return parse_page(response.text)
    else:
        return []

def clean_html_content(html_content):
    """
    Clean HTML content by removing tags, normalizing spaces, and unescaping entities.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        str: Cleaned text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
 
def scrape_article(url):
    """
    Scrape and parse an individual article.
    
    Args:
        url (str): URL of the article to scrape
        
    Returns:
        dict: Article data including title, date, category, content, and URL
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract article components
    title_tag = soup.find('h1', class_='page-title')
    title = clean_html_content(str(title_tag)) if title_tag else None

    date_tag = soup.find('time', class_='posted-on entry-date published updated')
    date_posted = clean_html_content(str(date_tag)) if date_tag else None

    category_tag = soup.find('a', class_='wh-breadcrumb__link ui-label-base', rel='category tag')
    category = clean_html_content(str(category_tag)) if category_tag else None

    body_content_section = soup.find('section', class_='body-content')
    content_tags = body_content_section.find_all('p') if body_content_section else []
    content = '\n\n'.join(clean_html_content(str(tag)) for tag in content_tags) if content_tags else None

    return {
        'title': title,
        'date_posted': date_posted,
        'category': category,
        'content': content,
        'url': url
    }

def scrape_briefing_room() -> int:
    """
    Main function to scrape the White House Briefing Room.
    
    Uses concurrent execution to scrape multiple pages simultaneously.
    Processes articles as they are found and stores them in MongoDB.
    
    Returns:
        int: Total number of URLs processed
    """
    page_number = 1
    max_workers = 10  # Number of concurrent scraping threads
    res = 0  # Counter for processed URLs
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Setup progress bar
        pbar = tqdm(total=0, desc="Pages Scraped", dynamic_ncols=True, bar_format='{desc}: {n}')
        future_to_page = {}
        processed_pages = set()
        
        # Submit initial batch of pages
        for i in range(max_workers):
            future = executor.submit(scrape_page, page_number)
            future_to_page[future] = page_number
            processed_pages.add(page_number)
            page_number += 1       
        
        # Process pages until no more are found
        while future_to_page:
            for future in concurrent.futures.as_completed(future_to_page):
                page_num = future_to_page.pop(future)       
                try:
                    links = future.result()
                    if links:
                        res += len(links)                                    
                        # Process each article found on the page
                        for link in links:
                            article_details = scrape_article(link)
                            insert_article(article_details)
                            
                        # Queue next page if not already processed
                        if page_number not in processed_pages:
                            future = executor.submit(scrape_page, page_number)
                            future_to_page[future] = page_number
                            page_number += 1
                        pbar.update(1)
                    else:
                        break    
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")          
        pbar.close() 
    return res

if __name__ == "__main__":
    visited = scrape_briefing_room()
    print(f"Scraping done with {visited} urls visited")
