import os
from pymongo import MongoClient
from dotenv import load_dotenv
from scrapers.whgov_scraper import scrape_briefing_room, WHArticle, collection

# Load environment variables
load_dotenv()

# MongoDB connection string
connection_string = os.getenv('MONGO_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['whgov']
collection = db['whbriefingroom']

def test_scraper():
    # Clear the collection to avoid duplicates during testing
    collection.delete_many({})
    
    # Run the scraper
    visited = scrape_briefing_room()
    print(f"Scraping done with {visited} urls visited")

    # Retrieve and print the articles from the database
    articles = collection.find()
    for article in articles:
        try:
            # Validate the article using the WHArticle model
            valid_article = WHArticle(**article)
            print(valid_article)
        except Exception as e:
            print(f"Validation error: {e}")

if __name__ == "__main__":
    test_scraper()
