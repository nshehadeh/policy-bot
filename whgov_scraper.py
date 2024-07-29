import requests
from bs4 import BeautifulSoup
import concurrent.futures

BASE_URL = 'https://www.whitehouse.gov/briefing-room/page/'

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
            future_to_page = {executor.submit(scrape_page, page_number): page_number for page_number in range(1, 3)} # replace with max pages
            for future in concurrent.futures.as_completed(future_to_page):
                page_number = future_to_page[future]
                try:
                    links = future.result()
                    if links:
                        visited_urls.extend(links)
                    print(f"Scraped page {page_number}")
                except Exception as e:
                    print(f"Error scraping page {page_number}: {e}")

scrape_briefing_room()

# Print the collected URLs
with open('visited_urls.txt', 'w') as file:
    for url in visited_urls:
        file.write(f"{url}\n")
    
