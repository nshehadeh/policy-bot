import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from pprint import pprint
from langchain.prompts import ChatPromptTemplate
from threading import Lock

# Abstract base classes
class BaseModel:
    def get_model(self):
        raise NotImplementedError

class BaseEmbeddings:
    def get_embeddings(self):
        raise NotImplementedError

class BaseVectorStore:
    def get_vector_store(self):
        raise NotImplementedError

class BasePromptTemplate:
    def get_prompt_template(self):
        raise NotImplementedError

# Concrete implementations
class OpenAIModel(BaseModel):
    def get_model(self):
        return ChatOpenAI(model="gpt-4o")

class OpenAIEmbeddingsModel(BaseEmbeddings):
    def get_embeddings(self):
        return OpenAIEmbeddings(model='text-embedding-3-small')

class PineconeVectorStoreModel(BaseVectorStore):
    def __init__(self, index_name, embeddings):
        self.index_name = index_name
        self.embeddings = embeddings

    def get_vector_store(self):
        return PineconeVectorStore(index_name=self.index_name, embedding=self.embeddings)

class SimplePromptTemplate(BasePromptTemplate):
    def get_prompt_template(self):
        template = """Answer the question using the context. Give a one line summary of the context metadata used at the end of your answer:
{context}

Question: {question}
"""
        return ChatPromptTemplate.from_template(template)

# Generator class
class Generator:
    def __init__(self, llm, retriever, prompt_template):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt_template
        self.rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def generate(self, question):
        return self.rag_chain.invoke(question)

# Singleton RAGSystem
class RAGSystem:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model: BaseModel, embeddings: BaseEmbeddings, vector_store: BaseVectorStore, prompt_template: BasePromptTemplate):
        if not hasattr(self, '_initialized'):  # Ensures __init__ is run only once
            load_dotenv()
            self._load_environment_variables()
            self.llm = model.get_model()
            self.embeddings = embeddings.get_embeddings()
            self.vector_store = vector_store.get_vector_store()
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 3}
            )
            self.prompt = prompt_template.get_prompt_template()
            self.generator = Generator(self.llm, self.retriever, self.prompt)
            self._initialized = True
    
    def _load_environment_variables(self):
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        os.environ["PINECONE_API_KEY"] = os.getenv('PINECONE_API_KEY')
    
    def query(self, question):
        return self.generator.generate(question)

# Example usage
if __name__ == "__main__":
    model = OpenAIModel()
    embeddings = OpenAIEmbeddingsModel()
    vector_store = PineconeVectorStoreModel(index_name="langchain-index", embeddings=embeddings.get_embeddings())
    prompt_template = SimplePromptTemplate()

    rag_system = RAGSystem(model, embeddings, vector_store, prompt_template)
    result = rag_system.query("What are Biden's tax policies for young adults")
    pprint(result)
