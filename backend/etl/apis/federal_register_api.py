import requests
from pymongo import MongoClient
import logging
import os
from dotenv import load_dotenv
import PyPDF2
from xml.etree import ElementTree
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Connection
def get_mongo_collection():
    try:
        connection_string = os.getenv('MONGO_CONNECTION_STRING')
        client = MongoClient(connection_string)
        db = client['govai']
        logging.info("Connected to MongoDB successfully.")
        return db['federal_registry']
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

# Federal Register API Configuration
BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"

# Fetch documents from the Federal Register API with pagination
def fetch_documents(start_date, end_date, per_page=100):
    all_documents = []
    page = 1  # Start with the first page

    while True:
        params = {
            "conditions[publication_date][gte]": start_date,
            "conditions[publication_date][lte]": end_date,
            "per_page": per_page,
            "page": page,
            "order": "newest",
        }

        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break  # Exit the loop if no more results

            all_documents.extend(results)
            logging.info(f"Fetched {len(results)} documents from page {page}.")
            page += 1  # Move to the next page

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from the API: {e}")
            raise

    logging.info(f"Total documents fetched: {len(all_documents)}.")
    return {"results": all_documents}

# Fetch raw text from the URL
def fetch_raw_text(raw_text_url):
    try:
        response = requests.get(raw_text_url)
        response.raise_for_status()
        raw_html = response.text
        # Clean the HTML content
        soup = BeautifulSoup(raw_html, "html.parser")
        clean_text = soup.get_text()
        return clean_text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch raw text from {raw_text_url}: {e}")
        return None

# Fetch and parse text from the full text XML URL
def fetch_full_text(full_text_xml_url):
    try:
        response = requests.get(full_text_xml_url)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        text = " ".join(element.text for element in root.iter() if element.text)
        return text
    except (requests.exceptions.RequestException, ElementTree.ParseError) as e:
        logging.error(f"Failed to fetch or parse full text from {full_text_xml_url}: {e}")
        return None

# Extract text from a PDF URL
def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
        with open("temp.pdf", "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        os.remove("temp.pdf")  # Clean up temporary file
        return text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download PDF from {pdf_url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Failed to extract text from PDF: {e}")
        return None

# Transform raw API data into a consistent format with text extraction
def transform(raw_data):
    try:
        documents = []
        raw_text_count = 0
        full_text_count = 0
        pdf_text_count = 0
        failed_text_count = 0

        for item in raw_data.get("results", []):
            raw_text = None
            if item.get("raw_text_url"):
                raw_text = fetch_raw_text(item["raw_text_url"])
                if raw_text:
                    raw_text_count += 1
            elif item.get("full_text_xml_url"):
                raw_text = fetch_full_text(item["full_text_xml_url"])
                if raw_text:
                    full_text_count += 1
            elif item.get("pdf_url"):
                raw_text = extract_text_from_pdf(item["pdf_url"])
                if raw_text:
                    pdf_text_count += 1

            if not raw_text:
                failed_text_count += 1

            documents.append({
                "document_number": item.get("document_number"),
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "publication_date": item.get("publication_date"),
                "type": item.get("type"),
                "html_url": item.get("html_url"),
                "pdf_url": item.get("pdf_url"),
                "public_inspection_pdf_url": item.get("public_inspection_pdf_url"),
                "full_text_xml_url": item.get("full_text_xml_url"),
                "raw_text_url": item.get("raw_text_url"),
                "raw_text": raw_text,  # Store extracted text
                "agencies": item.get("agencies", []),
                "excerpts": item.get("excerpts", []),
                # Placeholder for summarization
                "summary": None,  
                # Indicates if the document has been chunked
                "chunked": False, 
                # Indicates if embeddings are generated
                "embedded": False, 
                 # Timestamp of the last processing
                "processed_at": None,
            })

        logging.info(f"Text extraction summary: {raw_text_count} from raw_text_url, {full_text_count} from full_text_xml_url, {pdf_text_count} from pdf_url, {failed_text_count} failures.")
        logging.info(f"Transformed {len(documents)} documents with text extraction.")
        return documents
    except Exception as e:
        logging.error(f"Error during transformation: {e}")
        raise

# Load data into MongoDB
def load_into_mongo(data):
    try:
        collection = get_mongo_collection()
        for doc in data:
            collection.update_one(
                {"document_number": doc["document_number"]},
                {"$set": doc},
                upsert=True
            )
        logging.info(f"Loaded {len(data)} documents into MongoDB.")
    except Exception as e:
        logging.error(f"Failed to load data into MongoDB: {e}")
        raise

if __name__ == "__main__":
    import argparse

    # Argument parser for date range input
    parser = argparse.ArgumentParser(description="ETL script for Federal Register data.")
    parser.add_argument("--start_date", type=str, required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end_date", type=str, required=True, help="End date in YYYY-MM-DD format.")
    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date

    logging.info(f"Starting ETL process for data from {start_date} to {end_date}.")

    try:
        # Extract
        raw_data = fetch_documents(start_date, end_date)

        # Transform
        transformed_data = transform(raw_data)

        # Load
        load_into_mongo(transformed_data)

        logging.info("ETL process completed successfully.")
    except Exception as e:
        logging.error(f"ETL process failed: {e}")
