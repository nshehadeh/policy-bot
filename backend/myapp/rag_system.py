import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from threading import Lock
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from time import sleep
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
        raise NotImplementedError(
            "_validate_embedding_compatibility must be implemented in concrete vector store classes."
        )

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
        return OpenAIEmbeddings(model="text-embedding-3-small")


class PineconeVectorStoreModel(BaseVectorStore):
    def __init__(self, index_name, embeddings):
        self.index_name = index_name
        self.embeddings = embeddings
        self._validate_embedding_compatibility(embeddings)
        super().__init__(embeddings)

    def _validate_embedding_compatibility(self, embedding: OpenAIEmbeddings) -> bool:
        return embedding.model == self.embeddings.model

    def get_vector_store(self) -> PineconeVectorStore:
        return PineconeVectorStore(
            index_name=self.index_name, embedding=self.embeddings
        )


class QAPromptTemplate(BasePromptTemplate):
    def get_prompt_template(self) -> ChatPromptTemplate:
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise. It is required to provide a one line source of the context metadata used at the end of your answer."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        return prompt


class ContextPromptTemplate(BasePromptTemplate):
    def get_prompt_template(self) -> ChatPromptTemplate:
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        return contextualize_q_prompt


class QuerySearchPromptTemplate(BasePromptTemplate):
    def get_prompt_template(self) -> PromptTemplate:
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

        return PromptTemplate.from_template(template)


# Generator class
class Generator:
    def __init__(
        self,
        llm,
        retriever,
        qa_prompt_template,
        context_q_prompt_template,
        chat_history: ChatMessageHistory,
    ) -> None:
        self.llm = llm
        self.retriever = retriever
        self.qa_prompt = qa_prompt_template
        self.context_q_prompt = context_q_prompt_template
        self.chat_history = chat_history

        self.question_answer_chain = create_stuff_documents_chain(
            self.llm, self.qa_prompt
        )
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, self.context_q_prompt
        )
        self.rag_chain = create_retrieval_chain(
            self.history_aware_retriever, self.question_answer_chain
        )

        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def invoke(self, question):
        for chunk in self.conversational_rag_chain.stream({"input": question}):
            if "answer" in chunk:
                yield chunk["answer"]
                sleep(0.2)

    async def invoke_async(self, question):
        async for chunk in self.conversational_rag_chain.astream({"input": question}):
            if "answer" in chunk:
                yield chunk["answer"]
                await asyncio.sleep(0.1)

    def update_chat_history(self, new_chat_history: ChatMessageHistory) -> None:
        self.chat_history = new_chat_history

    def get_session_history(self) -> ChatMessageHistory:
        return self.chat_history


# Search Class
class Search:
    def __init__(self, llm, retriever, prompt_template):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt_template
        self.query_search_chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, question):
        """Handle search queries by expanding the query and retrieving relevant documents."""
        # TODO Add relevance scores
        try:
            expanded_query = self.query_search_chain.invoke(question)
            docs = self.retriever.invoke(expanded_query)
            results = []
            for doc in docs:
                doc_id = doc.metadata.get("id")
                if doc_id:
                    results.append(doc_id)
                if len(results) >= 6:
                    break
            return results

        except Exception as e:
            print(f"Search error: {str(e)}")
            return []


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

    def __init__(
        self,
        model: Optional[BaseModel] = None,
        embeddings: Optional[BaseEmbeddings] = None,
        vector_store: Optional[BaseVectorStore] = None,
        prompt_template: Optional[BasePromptTemplate] = None,
        chat_history: ChatMessageHistory = ChatMessageHistory(),
    ) -> None:
        if not hasattr(self, "_initialized"):
            load_dotenv()
            self._load_environment_variables()

            self.llm = (model or OpenAIModel()).get_model()
            self.embeddings = (embeddings or OpenAIEmbeddingsModel()).get_embeddings()
            self.vector_store = (
                vector_store
                or PineconeVectorStoreModel(
                    index_name="langchain-index", embeddings=self.embeddings
                )
            ).get_vector_store()
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity", search_kwargs={"k": 6}
            )
            self.qa_prompt = (
                prompt_template or QAPromptTemplate()
            ).get_prompt_template()
            self.context_prompt = ContextPromptTemplate().get_prompt_template()
            self.query_search_prompt = QuerySearchPromptTemplate().get_prompt_template()
            self.generator = Generator(
                self.llm,
                self.retriever,
                self.qa_prompt,
                self.context_prompt,
                chat_history,
            )

            self.search = Search(self.llm, self.retriever, self.query_search_prompt)
            self._initialized = True
            self.msg = ""

    def _load_environment_variables(self):
        if api_key := os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = api_key
        if pinecone_key := os.getenv("PINECONE_API_KEY"):
            os.environ["PINECONE_API_KEY"] = pinecone_key
        if langsmith_key := os.getenv("LANGSMITH_API_KEY"):
            os.environ["LANGSMITH_API_KEY"] = langsmith_key
        if os.getenv("LANGCHAIN_TRACING_V2"):
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    def update_llm(self, model: BaseModel) -> None:
        """Update the language model."""
        self.llm = model.get_model()
        self.generator.llm = self.llm

    async def handle_chat_query(self, question):
        """Handle chat-based queries using the generator for streaming responses."""
        try:
            logger.info("Processing chat query")
            async for generated_chunk in self.generator.invoke_async(question):
                yield generated_chunk
            logger.info("Successfully completed chat query")
        except Exception as e:
            logger.error(f"Error in chat query processing: {str(e)}")
            # Fallback response
            yield "I apologize, but I'm having trouble processing your request right now. Please try again."

    def handle_search_query(self, question):
        """Handle search queries with error handling and fallback"""
        try:
            logger.info("Processing search query")
            results = self.search.invoke(question)
            logger.info(f"Search completed successfully with {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in search query: {str(e)}")
            # Empty fallback
            return []

    def load_memory(self, chat_history: ChatMessageHistory) -> None:
        """Load chat history into memory."""
        self.generator.update_chat_history(chat_history)
