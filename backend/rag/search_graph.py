"""Search graph implementation for document retrieval."""

from typing import Optional
from threading import Lock
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END

from .base import (
    BaseRAGGraph,
    BaseModel,
    BaseEmbeddings,
    BaseVectorStore,
    QuerySearchPromptTemplate,
)


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
        search_prompt: Optional[SearchPromptTemplate] = None,
    ):
        if not hasattr(self, "_initialized"):
            super().__init__(model, embeddings, vector_store)

            # Initialize search-specific prompt
            self.search_prompt = (
                search_prompt or SearchPromptTemplate()
            ).get_prompt_template()
            self.search_chain = self.search_prompt | self.llm | StrOutputParser()

            self.workflow = self._setup_workflow()
            self._initialized = True

    def _expand_query(self, state):
        """Expand the search query for better retrieval."""
        messages = state["messages"]
        query = messages[0].content
        response = self.search_chain.invoke({"query": query})
        return {"messages": [HumanMessage(content=response)]}

    def _setup_workflow(self) -> StateGraph:
        """Set up the search workflow."""
        workflow = StateGraph(MessagesState)

        # Add nodes
        workflow.add_node("expand_query", self._expand_query)
        workflow.add_node("retrieve", self.retrieve)

        # Add edges
        workflow.set_entry_point("expand_query")
        workflow.add_edge("expand_query", "retrieve")
        workflow.add_edge("retrieve", END)

        return workflow

    def process_query(self, query: str, context: Optional[dict] = None):
        """Process a search query through the workflow.

        Args:
            query: The search query
            context: Optional context from chat session
        """
        state = {"messages": [HumanMessage(content=query)]}
        if context:
            state["context"] = context
        return self.workflow.invoke(state)
