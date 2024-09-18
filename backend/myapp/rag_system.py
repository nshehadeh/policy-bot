import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from pprint import pprint
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from threading import Lock
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

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

class QAPromptTemplate(BasePromptTemplate):
    def get_prompt_template(self):
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise. Give a one line summary of the context metadata used at the end of your answer"
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
    def get_prompt_template(self):
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

# Generator class
class Generator:
    def __init__(self, llm, retriever, qa_prompt_template, context_q_prompt_template, chat_history: ChatMessageHistory):
        self.llm = llm
        self.retriever = retriever
        self.qa_prompt = qa_prompt_template
        self.context_q_prompt = context_q_prompt_template
        self.chat_history = chat_history
        
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
        self.history_aware_retriever = create_history_aware_retriever(llm, retriever, self.context_q_prompt)

        # RAG-Fusion init
        self.rag_fusion_prompt = self._init_rag_fusion_prompt()
        self.generate_queries = (
            self.rag_fusion_prompt 
            | ChatOpenAI(temperature=0)
            | StrOutputParser() 
            | (lambda x: x.split("\n"))
        )
        
        self.retrieval_chain_rag_fusion = self.generate_queries | retriever.map() | self._reciprocal_rank_fusion
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)
        
        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer", 
        )

    def _init_rag_fusion_prompt(self):
        template = """You are a helpful assistant that generates multiple search queries based on a single input query. \n
                      Generate multiple search queries related to: {question} \n
                      Output (4 queries):"""
        return ChatPromptTemplate.from_template(template)

    def _reciprocal_rank_fusion(self, results: list[list], k=60):
        # Reciprocal rank fusion for re-ranking documents
        fused_scores = {}
        for docs in results:
            for rank, doc in enumerate(docs):
                doc_str = dumps(doc)
                if doc_str not in fused_scores:
                    fused_scores[doc_str] = 0
                fused_scores[doc_str] += 1 / (rank + k)
        
        reranked_results = [
            (loads(doc), score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        return reranked_results

    def invoke(self, question):
        # Use RAG-Fusion retrieval chain for getting documents
        docs = self.retrieval_chain_rag_fusion.invoke({"question": question})
        
        return self.conversational_rag_chain.invoke(
            {"input": question, "context": docs},
        )["answer"]
    
    def update_chat_history(self, new_chat_history: ChatMessageHistory):
        self.chat_history = new_chat_history
        
    def get_session_history(self):
        return self.chat_history

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
                 prompt_template: BasePromptTemplate = None,
                 chat_history: ChatMessageHistory = ChatMessageHistory()):
        if not hasattr(self, '_initialized'):  # Ensures __init__ is run only once
            load_dotenv()
            self._load_environment_variables()

            self.llm = (model or OpenAIModel()).get_model()
            self.embeddings = (embeddings or OpenAIEmbeddingsModel()).get_embeddings()
            self.vector_store = (vector_store or PineconeVectorStoreModel(index_name="langchain-index", embeddings=self.embeddings)).get_vector_store()
            # TODO make and improve retriever class by making context aware, getting full documents from mongodb, etc
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 3}
            )
            self.qa_prompt = (prompt_template or QAPromptTemplate()).get_prompt_template()
            self.context_prompt = ContextPromptTemplate().get_prompt_template()
            self.generator = Generator(self.llm, self.retriever,  self.qa_prompt, self.context_prompt, chat_history)
            self._initialized = True
            self.msg = ""

    def _load_environment_variables(self):
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        os.environ["PINECONE_API_KEY"] = os.getenv('PINECONE_API_KEY')

    def update_llm(self, model: BaseModel):
        self.llm = model.get_model()
        self.generator.llm = self.llm 

    def handle_query(self, question):
        generated = self.generator.invoke(question)
        # self.generator.memory.save_context({"input": question}, {"output": generated})
        return f"{self.msg} {generated}"
    
    # TODO can integrate with ChatMessageHistory eventualy instead of JSON objects,
    # would just have to adjust frontend, specifically with postgresql class
    
    # builds new chatmessagehistory based on messages
    # can customize this later
    def load_memory(self, chat_history: ChatMessageHistory):
        self.generator.update_chat_history(chat_history)
