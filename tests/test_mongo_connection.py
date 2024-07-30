import os
from pymongo import MongoClient
from dotenv import load_dotenv


def test_mongo_connection():
    print("Loading environment variables...")
    # Load environment variables
    load_dotenv()
    connection_string = os.getenv('MONGO_CONNECTION_STRING')
    if not connection_string:
        print("MongoDB connection string not found in environment variables.")
        return
    
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(connection_string)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

if __name__ == "__main__":
    print("Starting MongoDB connection test...")
    test_mongo_connection()
    print("Done")

