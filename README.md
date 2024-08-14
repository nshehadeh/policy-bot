# PolicyBot
### Political LLM App 

To run:
- Start React server in in frontend/ with yarn start, if issues run: rm -rf node_modules --> yarn install --> yarn start
- Start Django server in backend/ with python manage.py makemigrations --> python manage.py migrate --> python manage.py runserver
- App will run on localhost:3000, Django admin: http://127.0.0.1:8000/admin/
- Uses postgresql hosted locally, change all variables in env for databases and API keys

Currently Working on:
- Loading history when old chats are selected
- Improving RAG

## Tech Stack
### In Progress

| Component                | Description                                    |
|--------------------------|------------------------------------------------|
| **Django Backend**       | REST API, User Auth, LLM Integration, RAG System|
| **LangChain & ChatGPT**  | Query Processing, Response Generation          |
| **MongoDB**              | Document Storage, User Data, Conversation History|

### Future

| Component                | Description                                    |
|--------------------------|------------------------------------------------|
| **React Frontend**       | UI Components, State Management, Chat UI       |
| **Deployment & Hosting** | AWS, Docker, Kubernetes                        |
| **CI/CD Pipeline**       | GitHub Actions, Jenkins                        |



