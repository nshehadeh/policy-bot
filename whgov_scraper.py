from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from dotenv import load_dotenv
import os
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm
from html import unescape
import re



# TODO Generate proper method comments using chatgpt
# Load .env environment variables
load_dotenv()
# MongoDB connection str
connection_string = os.getenv('MONGO_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['whgov']
collection = db['whbriefingroom']

BASE_URL = 'https://www.whitehouse.gov/briefing-room/page/'

# Categories to scrape within Briefing Room
CATEGORIES = [
    'blog', 'disclosures', 'legislation', 'presidential-actions', 
    'press-briefings', 'speeches-remarks', 'statements-releases'
]

class WHArticle(BaseModel):
    title: str
    # Raises validation error if type is not a category
    category: Literal['blog', 'disclosures', 'legislation', 'presidential-actions', 'press-briefings', 'speeches-remarks', 'statements-releases']
    date_posted: str
    text: str
    url: str
    source: str = Field(default="White House Gov Briefing Room")


def insert_article(article_data):
    """Inserts an article into the MongoDB collection

    Args:
        article (dictionary): dictionary containing the information necessary for an article schema and insertion to the database
    """
    try:
        article = WHArticle(**article_data)
        # model_dump converts pydantic model to dictionary
        collection.insert_one(article.model_dump())
    except ValidationError as e:
        print(f"Validation error inserting an article: {e}")    
        
def fetch_url(url):
    response = requests.get(url)
    # No sleep for now, possibly implement this if you're getting errors/ temp bans from website
    # time.sleep(random.uniform(1, 3))  # Sleep for a random interval between 1 and 3 seconds
    return response

# TODO Actually go to article and parse information now
def parse_page(content):
    """Parses multiple article urls from a briefing room page

    Args:
        content (str): url of the page

    Returns:
        list: list of urls found on the briefing page
    """
    soup = BeautifulSoup(content, 'html.parser')
    articles = soup.find_all('article', class_='news-item')
    links = []
    for article in articles:
        link = article.find('a', class_='news-item__title')['href']
        links.append(link)
    return links

def scrape_page(page_number):
    url = f"{BASE_URL}{page_number}/"
    response = fetch_url(url)
    if response.status_code == 200:
        return parse_page(response.text)
    else:
        return []

def clean_html_content(html_content):
    # Initialize BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text from HTML
    text = soup.get_text()

    # Unescape HTML entities
    text = unescape(text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text
 
#TODO if necessary in the future, add a determine_author_function possibly using LLMs

def scrape_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract and clean title
    title_tag = soup.find('h1', class_='page-title')
    title = clean_html_content(str(title_tag)) if title_tag else None

    # Extract and clean date
    date_tag = soup.find('time', class_='posted-on entry-date published updated')
    date = clean_html_content(str(date_tag)) if date_tag else None

    # Extract and clean category
    category_tag = soup.find('a', class_='wh-breadcrumb__link ui-label-base', rel='category tag')
    category = clean_html_content(str(category_tag)) if category_tag else None

    # Extract and clean content
    content_tags = soup.find_all('p')
    content = '\n\n'.join(clean_html_content(str(tag)) for tag in content_tags) if content_tags else None

    return {
        'title': title,
        'date': date,
        'category': category,
        'content': content
    }


def scrape_briefing_room() -> int:
    page_number = 1
    max_workers = 15
    res = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        pbar = tqdm(total=0, desc="Pages Scraped", dynamic_ncols=True, bar_format='{desc}: {n}')
        future_to_page = {}
        processed_pages = set()

        # Submit the initial batch of pages
        for i in range(max_workers):
            future = executor.submit(scrape_page, page_number)
            future_to_page[future] = page_number
            processed_pages.add(page_number)
            page_number += 1
            
        # Continue batching pages until no pages are left
        while future_to_page:
            for future in concurrent.futures.as_completed(future_to_page):
                # Save page_num for printing & error purposes
                page_num = future_to_page.pop(future)
                
                try:
                    links = future.result()
                    if links:
                        # Resulting links from the page
                        res += len(links)
                                                
                        # Scrape article from each article link and insert into the database
                        for link in links:
                            article_details = scrape_article(link)
                            insert_article(article_details)

                        # Submit the next page for scraping
                        if page_number not in processed_pages:
                            future = executor.submit(scrape_page, page_number)
                            future_to_page[future] = page_number
                            page_number += 1
                        
                                        # Update the progress bar
                        pbar.update(1)
                    else:
                        # print(f"No more articles found at page {page_num}. Stopping.")
                        # Exit while loop
                        break
                    
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")
                
        pbar.close()
        
    return res

if __name__ == "__main__":
    # Print num of URLS visited just to check
    visited = scrape_briefing_room()
    print(f"Scraping done with {visited} urls visited")

