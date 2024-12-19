"""
White House Briefing Room Document Summarizer

This module processes White House briefing room documents stored in MongoDB by generating
concise summaries.

Dependencies:
    - OpenAI API key in environment variables
    - MongoDB connection string in environment variables
    - langchain_openai for GPT model interaction
    - pymongo for database operations
"""

import logging
import os
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Configure logging with timestamp and log level
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP request logging from OpenAI and httpx
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize LLM model for text summarization
llm = ChatOpenAI(model="gpt-4o-mini")


def generate_summary(text):
    """
    Generate a concise summary of the provided text using GPT model.

    Args:
        text (str): The input text to be summarized.

    Returns:
        str or None: A summary of the input text in 4 sentences or less.
                    Returns None if summarization fails.
    """
    try:
        # Define the prompt for the GPT model
        prompt = f"""
        You are a summarization assistant. 
        Summarize the following text in no more than four sentences.
        Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness. 
        Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects. 
        Rely strictly on the provided text, without including external information. 
        The summary will be displayed a quick card, giving users an overview of the document.
        Do not use more than 4 sentences.
        
        {text}"""

        # Invoke the GPT model to generate a summary
        response = llm.invoke(prompt)

        # Return the generated summary
        return response.content
    except Exception as e:
        # Log any errors that occur during summarization
        logger.error(f"Error generating summary: {str(e)}")
        return None


def get_mongo_collection():
    """
    Establish connection to MongoDB and return the White House briefing room collection.

    Returns:
        pymongo.collection.Collection: MongoDB collection object for briefing room documents.

    Raises:
        Exception: If connection to MongoDB fails.
    """
    try:
        # Get the MongoDB connection string from environment variables
        connection_string = os.getenv("MONGO_CONNECTION_STRING")

        # Establish a connection to MongoDB
        client = MongoClient(connection_string)

        # Select the database and collection for briefing room documents
        db = client["WTP"]
        logging.info("Connected to MongoDB successfully.")

        # Return mongodb collection
        return db["whbriefingroom"]

    except Exception as e:
        # Log any errors that occur during connection
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise


def summarize_documents():
    """
    Process documents in the MongoDB collection that lack summaries.

    This function:
    1. Retrieves documents without summaries in batches
    2. Generates a summary for each document's content
    3. Updates the documents with their new summaries
    4. Handles errors and provides progress tracking

    The batch processing approach helps manage memory usage and provides
    better error isolation.
    """
    try:
        # Initialize the MongoDB client
        collection = get_mongo_collection()

        # Define a query to find documents without summaries
        query = {"content": {"$exists": True}, "summary": {"$exists": False}}

        # Get the total number of documents to process
        total_docs = collection.count_documents(query)
        logger.info(f"Found {total_docs} documents to process")

        batch_size = 50
        processed = 0

        with tqdm(total=total_docs, desc="Summarizing documents") as pbar:
            # Initialize the last ID for pagination
            last_id = None

            # Process documents in batches
            while processed < total_docs:
                # Build a query with pagination
                batch_query = query.copy()
                if last_id:
                    batch_query["_id"] = {"$gt": last_id}

                # Retrieve a batch of documents
                batch = list(
                    collection.find(batch_query).sort("_id", 1).limit(batch_size)
                )

                if not batch:
                    break

                # Process each document in the batch
                for doc in batch:
                    try:
                        content = doc.get("content")
                        if not content:
                            logger.warning(
                                f"Document {doc['_id']} has no content, skipping"
                            )
                            continue

                        # Generate a summary for the document
                        summary = generate_summary(content)
                        if summary:
                            # Update document with summary
                            collection.update_one(
                                {"_id": doc["_id"]}, {"$set": {"summary": summary}}
                            )
                            processed += 1
                            pbar.update(1)

                            if processed % batch_size == 0:
                                logger.info(
                                    f"Processed {processed}/{total_docs} documents"
                                )
                        else:
                            logger.warning(
                                f"Failed to generate summary for document {doc['_id']}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error processing document {doc['_id']}: {str(e)}"
                        )
                        continue

                # Update the last ID for the next batch
                last_id = batch[-1]["_id"]
                logger.info(
                    f"Completed batch. Total processed: {processed}/{total_docs}"
                )

        logger.info(f"Completed processing. Total documents processed: {processed}")

    except Exception as e:
        logger.error(f"Database error: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting document summarization process")
    summarize_documents()
    logger.info("Document summarization process completed")
