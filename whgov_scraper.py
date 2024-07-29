from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from dotenv import load_dotenv
import os

# Load .env environment variables
load_dotenv()
# MongoDB connection str
"""
connection_string = os.getenv('MONGO_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['whgov']
BASE_URL = 'https://www.whitehouse.gov/briefing-room/page/'
"""
# Categories to scrape within Briefing Room
CATEGORIES = [
    'blog', 'disclosures', 'legislation', 'presidential-actions', 
    'press-briefings', 'speeches-remarks', 'statements-releases'
]

visited_urls = []

def fetch_url(url):
    response = requests.get(url)
    # No sleep for now, possibly implement this if you're getting errors/ temp bans from website
    # time.sleep(random.uniform(1, 3))  # Sleep for a random interval between 1 and 3 seconds
    return response

def parse_page(content):
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

#TODO implement adaptable for unknown number of pages aka make it dynamic with how many workers are being used
def scrape_briefing_room():
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures_to_page = {}
            while True:
                future = executor.submit(scrape_page, page_number)
                futures_to_page[future] = page_number
                for result in concurrent.futures.as_completed(futures_to_page):
                    page_number = futures_to_page[result]
                    try:
                        links = result.result()
                        if links:
                            visited_urls.extend(links)
                        print(f"Scraped page {page_number}")
                        page_number+=1
                    except Exception as e:
                        print(f"Error scraping page {page_number}: {e}")

scrape_briefing_room()

# Print the collected URLs
with open('visited_urls.txt', 'w') as file:
    file.write(str(len(visited_urls)))
    
