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
    def __init__(self, embedding):
        self._validate_embedding_compatibility(embedding)

    def _validate_embedding_compatibility(self, embedding):
        raise NotImplementedError("_validate_embedding_compatibility must be implemented in concrete vector store classes.")

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
        super().__init__(embeddings)
        self.index_name = index_name
        self.embeddings = embeddings

    def _validate_embedding_compatibility(self, embeddings):
        """
        Checks if the embedding model is compatible with the Pinecone vector store.
        Raises an exception if the embedding size does not match the vector store's configuration.
        
        # embedding_dim = something
        # vector_dim = something 
        
        if embedding_dim != vector_dim:
            raise ValueError(
                f"The embedding size ({embedding_dim}) does not match the Pinecone vector store's dimensionality ({vector_dim}). "
                "The embedding model and vector store must be compatible."
            )
        """
        pass

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
# Can eventually improve on configuration management and concurrency
class RAGSystem:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, 
                 model: BaseModel = None, 
                 embeddings: BaseEmbeddings = None, 
                 vector_store: BaseVectorStore = None, 
                 prompt_template: BasePromptTemplate = None):
        if not hasattr(self, '_initialized'):  # Ensures __init__ is run only once
            load_dotenv()
            self._load_environment_variables()

            # Use default values if none are provided
            self.llm = (model or OpenAIModel()).get_model()
            self.embeddings = (embeddings or OpenAIEmbeddingsModel()).get_embeddings()
            self.vector_store = (vector_store or PineconeVectorStoreModel(index_name="langchain-index", embeddings=self.embeddings)).get_vector_store()
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 3}
            )
            self.prompt = (prompt_template or SimplePromptTemplate()).get_prompt_template()
            self.generator = Generator(self.llm, self.retriever, self.prompt)
            self._initialized = True
            self.msg = "I, the policy bot, have decided to tell you:"

    def _load_environment_variables(self):
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        os.environ["PINECONE_API_KEY"] = os.getenv('PINECONE_API_KEY')

    def update_llm(self, model: BaseModel):
        self.llm = model.get_model()
        self.generator.llm = self.llm 


    def handle_query(self, question):
        generated = self.generator.generate(question)
        return f"{self.msg} {generated}"
