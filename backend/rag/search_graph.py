"""Search graph implementation for document retrieval."""

from typing import Optional, List, Literal
from threading import Lock
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import MessagesState, StateGraph
from langchain_pinecone import PineconeVectorStore
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, START
from langchain.tools.retriever import create_retriever_tool
from pydantic import BaseModel, Field
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from IPython.display import Image



from .base import (
    BaseRAGGraph,
    BaseModel,
    BaseEmbeddings,
    BaseVectorStore,
    QuerySearchPromptTemplate,
    RewritePromptTemplate,
    GenerateAnswerPromptTemplate,
    DirectResponsePromptTemplate,
    GraderPromptTemplate
)

class ExtState(MessagesState):
    doc_ids: list

class VectorStoreRetriever(BaseRetriever):
    """Sync wrapper for vector store retrieval."""
    
    vector_store: PineconeVectorStore

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async retrieval of relevant documents."""
        docs = await self.vector_store.asimilarity_search(query, k=6)
        return docs

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Sync retrieval of relevant documents."""
        docs = self.vector_store.similarity_search(query, k=6)
        print(f"{len(docs)} documents retrieved in retriever")
        return docs
    
class SearchGraph(BaseRAGGraph):
    """Singleton search graph for document retrieval."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model: Optional[BaseModel] = None,
        embeddings: Optional[BaseEmbeddings] = None,
        vector_store: Optional[BaseVectorStore] = None,
        search_prompt: Optional[QuerySearchPromptTemplate] = None,
    ):
        if not hasattr(self, "_initialized"):
            super().__init__(model, embeddings, vector_store)

            # Initialize prompts
            self.search_prompt = QuerySearchPromptTemplate().get_prompt_template()
            self.rewrite_prompt = RewritePromptTemplate().get_prompt_template()
            self.grader_prompt = GraderPromptTemplate().get_prompt_template()

            # Create sync retriever
            self.sync_retriever = VectorStoreRetriever(vector_store=self.vector_store)
            self.retrieve_tool = create_retriever_tool(
                retriever=self.sync_retriever,
                name="search_documents",
                description="Search through documents to find relevant information"
            )

            # Initialize search state
            self.max_retrieval_attempts = 3
            self.retrieval_attempts = 0
            
            self.graph = self._setup_workflow()
            self._initialized = True

    def _expand_query(self, state):
        """Expand the search query for better retrieval."""
        messages = state["messages"]
        query = messages[0].content
        search_chain = self.search_prompt | self.llm | StrOutputParser()
        response = search_chain.invoke({"query": query})
        return {"messages":[response]}

    def _retrieve(self, state):
        """Decide whether to retrieve or respond."""
        print("Query: ", state["messages"][-1].content)
        documents = self.retrieve_tool.invoke(state["messages"][-1].content)
        print(f"{len(documents)} documents retrieved")
        print(f"Document type: {type(documents)}")
        return {"doc_ids": [doc.metadata["id"] for doc in documents]}
    
    def _setup_workflow(self) -> StateGraph:
        """Set up the search workflow with conditional branching."""
        workflow = StateGraph(ExtState)

        # Add nodes
        workflow.add_node("expand_query", self._expand_query)
        workflow.add_node("retrieve", self._retrieve)
        #workflow.add_node("retrieve", tools)
        #workflow.add_node("rewrite", self._rewrite)
        #workflow.add_node("respond", self._respond)

        # Add edges with conditional branching
        workflow.add_edge(START, "expand_query")
        workflow.add_edge("expand_query", "retrieve")
        workflow.add_edge("retrieve", END)
        return workflow.compile()
        
    def get_compiled_graph(self):
        return self.graph
    
    def display(self):
        """Override string representation to display graph visualization."""
        return Image(self.get_compiled_graph().get_graph(xray=True).draw_mermaid_png())
    
    def process_query(self, query: str, context: Optional[dict] = None):
        """Process a search query through the workflow.

        Args:
            query: The search query
            context: Optional context from chat session
        """
        # self.retrieval_attempts = 0  # Reset counter
        inputs = {"messages": [HumanMessage(content=query)], "doc_ids": []}
        for state, meta in self.graph.stream(inputs, stream_mode="values"):
            print(f"State: {state}, Meta: {meta}")