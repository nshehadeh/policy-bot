"""Base classes and shared functionality for RAG system."""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class BaseLLMModel:
    """Base interface for language models."""

    def get_model(self):
        raise NotImplementedError


class BaseEmbeddings:
    """Base interface for text embedding models."""

    def get_embeddings(self):
        raise NotImplementedError


class BaseVectorStore:
    """Base interface for vector storage and retrieval."""

    def __init__(self, embedding):
        self._validate_embedding_compatibility(embedding)

    def _validate_embedding_compatibility(self, embedding):
        raise NotImplementedError

    def get_vector_store(self):
        raise NotImplementedError


class OpenAIModel(BaseLLMModel):
    """OpenAI GPT model implementation."""

    def get_model(self):
        return ChatOpenAI(model="gpt-4", temperature=0)


class OpenAIEmbeddingsModel(BaseEmbeddings):
    """OpenAI text embedding model implementation."""

    def get_embeddings(self):
        return OpenAIEmbeddings(model="text-embedding-3-small")


class PineconeVectorStoreModel(BaseVectorStore):
    """Pinecone vector store implementation."""

    def __init__(self, index_name: str, embeddings):
        super().__init__(embeddings)
        self.index_name = index_name
        self.embeddings = embeddings

    def _validate_embedding_compatibility(self, embedding) -> bool:
        if not isinstance(embedding, OpenAIEmbeddings):
            raise ValueError("PineconeVectorStore requires OpenAIEmbeddings")

    def get_vector_store(self) -> PineconeVectorStore:
        return PineconeVectorStore(
            index_name=self.index_name, embedding=self.embeddings
        )


class BasePromptTemplate:
    """Base interface for prompt templates."""

    def get_prompt_template(self):
        raise NotImplementedError


class HistoryPromptTemplate(BasePromptTemplate):
    """Template for processing chat history context."""

    def get_prompt_template(self) -> PromptTemplate:
        """Returns template for reformulating questions with context."""
        template = """Given a chat history and the latest user question 
        which might reference context in the chat history, 
        formulate a standalone question which can be understood 
        without the chat history. Do NOT answer the question, 
        just reformulate it if needed and otherwise return it as is. 
        Here is the chat history: \n\n {chat_history} \n\n
        Here is the latest user question: {question} \n\n
        """
        return PromptTemplate(
            template=template, input_variables=["chat_history", "question"]
        )


class GraderPromptTemplate(BasePromptTemplate):
    """Template for grading document relevance."""

    def get_prompt_template(self) -> PromptTemplate:
        """Returns template for grading document relevance."""
        template = """You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. Be extremely liberal in your judgement. Lean more towards giving yes if the document is a little relevant. \n"""
        return PromptTemplate(
            template=template, input_variables=["context", "question"]
        )


class RewritePromptTemplate(BasePromptTemplate):
    """Template for rewriting queries."""

    def get_prompt_template(self) -> PromptTemplate:
        """Returns template for query rewriting."""
        template = """Look at the input and try to reason about the underlying semantic intent / meaning. \n 
        Here is the initial question:
        \n ------- \n
        {question} 
        \n ------- \n
        Formulate a new question that is specific and deatiled to help with document retrieval. 
        Focus on key terms and concepts that might appear in relevant documents: """
        return PromptTemplate(template=template, input_variables=["question"])


class GenerateAnswerPromptTemplate(BasePromptTemplate):
    """Template for answer generation."""

    def get_prompt_template(self) -> PromptTemplate:
        """Returns template for answer generation."""
        template="""You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, say that you don't know. Use three sentences maximum and keep the answer concise. \n 
        Here is the original question: \n\n {question} \n\n
        Here are the retrieved context documents: {context} \n\n
        Give a one line summary of the context metadata used at the end of your answer."""
        return PromptTemplate(
            template=template,
            input_variables=["question", "context"]
        )


class QuerySearchPromptTemplate(BasePromptTemplate):
    """Template for expanding search queries with policy-specific context."""

    def get_prompt_template(self) -> PromptTemplate:
        """Returns template for query expansion with policy focus."""
        template = """You are an expert at expanding search queries to find relevant policy documents. 
            Given a simple query, expand it into a detailed search query that would help find relevant policy documents.
            Focus on including:
            - Related policy areas
            - Relevant stakeholders
            - Key terminology
            - Common policy frameworks
            - Related regulations or guidelines

            Query: {query}
            
            Expanded search query (be concise but comprehensive):"""

        return PromptTemplate(template = template, input_variables=["query"])

class DirectResponsePromptTemplate(BasePromptTemplate):
    
    """Template for generating a direct response."""
    def get_prompt_template(self) -> PromptTemplate:
        template="""You are a focused assistant that only provides brief, targeted responses.
        Provide a two sentence response that politely explains you can only answer questions about the specific content in our knowledge base which provides information about American policy .
        Do not provide any other information or engage in general conversation.
        
        User question: {question}
        
        One sentence response:"""
        
        return PromptTemplate(template=template, input_variables=["question"])
    

class BaseRAGGraph:
    """Base class for RAG graphs with common initialization."""

    def __init__(
        self,
        model: Optional[BaseLLMModel] = None,
        embeddings: Optional[BaseEmbeddings] = None,
        vector_store: Optional[BaseVectorStore] = None,
    ):
        self._load_environment_variables()
        self.llm = (model or OpenAIModel()).get_model()
        self.embeddings = (embeddings or OpenAIEmbeddingsModel()).get_embeddings()
        self.vector_store = (
            vector_store
            or PineconeVectorStoreModel(
                index_name="langchain-index", embeddings=self.embeddings
            )
        ).get_vector_store()

    def _load_environment_variables(self):
        """Load and validate required API keys."""
        load_dotenv()
        required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY", "LANGSMITH_API_KEY"]
        for var in required_vars:
            if value := os.getenv(var):
                os.environ[var] = value
            else:
                raise ValueError(f"Missing required environment variable: {var}")

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
