# PolicyBot
Political LLM App 

- Web scraper for whitehouse.gov's briefing room documents (~10,000) that saves to MongoDB NoSQL database
- Indexer for embedding documents and saving to MongoDB Atlas Vector Database or Pinecone Database
- Retriver for Pinecone Vector Database

Currently Working on:
- ipynb --> OOP
- Django REST Framework

## Tech Stack
### In Progress
+---------------------------+
|       React Frontend      |
|  (UI Components, State    |
|    Management, Chat UI)   |
+------------+--------------+
             |
             v
+------------+--------------+
|        Django Backend     |
| (REST API, User Auth, LLM |
|   Integration, RAG System)|
+------------+--------------+
             |
             v
+------------+--------------+
|  LangChain & ChatGPT      |
|  (Query Processing,       |
|  Response Generation)     |
+------------+--------------+
             |
             v
+------------+--------------+
|         MongoDB           |
| (Document Storage, User   |
| Data, Conversation History)|
+------------+--------------+

### Future

+---------------------------+
|    Deployment & Hosting   |
|  (AWS, Docker, Kubernetes)|
+---------------------------+

+---------------------------+
|      CI/CD Pipeline       |
|  (GitHub Actions, Jenkins)|
+---------------------------+