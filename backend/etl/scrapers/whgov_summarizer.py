import logging
import os
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress OpenAI HTTP request logging
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize LLM for summarization
llm = ChatOpenAI(model="gpt-4o-mini")

def generate_summary(text):
    try:
        prompt = f"""
        You are a summarization assistant. 
        Summarize the following text in no more than four sentences.
        Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness. 
        Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects. 
        Rely strictly on the provided text, without including external information. 
        The summary will be displayed a quick card, giving users an overview of the document.
        Do not use more than 4 sentences.
        
        {text}"""
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return None

# MongoDB Connection
def get_mongo_collection():
    try:
        connection_string = os.getenv('MONGO_CONNECTION_STRING')
        client = MongoClient(connection_string)
        db = client['WTP']
        logging.info("Connected to MongoDB successfully.")
        return db['whbriefingroom']
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise
    
def summarize_documents():
    """
    Retrieve all documents from the database, generate summaries for their content,
    and update them with the new summary field.
    """
    try:
        # Initialize MongoDB client
        collection = get_mongo_collection()
        
        # Get total document count for progress tracking
        total_docs = collection.count_documents({})
        logger.info(f"Found {total_docs} documents to process")
        
        # Process documents in batches
        batch_size = 500
        processed = 0
        
        # Get all documents that don't have a summary yet
        cursor = collection.find(
            {"content": {"$exists": True}, "summary": {"$exists": False}},
            {"_id": 1, "content": 1}
        )
        
        for doc in tqdm(cursor, total=total_docs, desc="Summarizing documents"):
            try:
                content = doc.get('content')
                if not content:
                    logger.warning(f"Document {doc['_id']} has no content, skipping")
                    continue
                
                # Generate summary
                summary = generate_summary(content)
                if summary:
                    # Update document with summary
                    collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"summary": summary}}
                    )
                    
                    processed += 1
                    if processed % batch_size == 0:
                        logger.info(f"Processed {processed}/{total_docs} documents")
                else:
                    logger.warning(f"Failed to generate summary for document {doc['_id']}")
                
            except Exception as e:
                logger.error(f"Error processing document {doc['_id']}: {str(e)}")
                continue
        
        logger.info(f"Completed processing. Total documents processed: {processed}")
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting document summarization process")
    summarize_documents()
    logger.info("Document summarization process completed")