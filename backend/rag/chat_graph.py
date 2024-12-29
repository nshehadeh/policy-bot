"""Chat graph implementation for conversational RAG."""

from typing import Optional, Literal, AsyncGenerator, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, START
from langchain_community.chat_message_histories import ChatMessageHistory
from IPython.display import Image
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain.tools.retriever import create_retriever_tool
from IPython.display import Image
from pydantic import BaseModel, Field
import asyncio


from .base import (
    BaseRAGGraph,
    BaseLLMModel,
    BaseEmbeddings,
    BaseVectorStore,
    VectorStoreRetriever,
    HistoryPromptTemplate,
    RewritePromptTemplate,
    GenerateAnswerPromptTemplate,
    DirectResponsePromptTemplate,
    GraderPromptTemplate
)

"""
def create_retrieve_tool(vector_store: BaseVectorStore):
    #Create a retrieve tool bound to a specific vector store.
    @tool(response_format="content_and_artifact")
    async def retrieve(query: str) -> tuple:
        #Retrieve relevant documents.
        retrieved_docs = await vector_store.similarity_search(query, k=6)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs
    return retrieve

"""
class VectorStoreRetriever(BaseRetriever):
    """Async wrapper for vector store retrieval."""
    
    vector_store: PineconeVectorStore

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async retrieval of relevant documents."""
        docs = await self.vector_store.asimilarity_search(query, k=6)
        return docs

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Sync version - not used but required by interface."""
        docs = self.vector_store.similarity_search(query, k=6)
        return docs
    

    
class ChatGraph(BaseRAGGraph):
    """Handles conversational RAG with history."""

    def __init__(
        self,
        model: Optional[BaseLLMModel] = None,
        embeddings: Optional[BaseEmbeddings] = None,
        vector_store: Optional[BaseVectorStore] = None,
        chat_history: ChatMessageHistory = ChatMessageHistory(),
        history_prompt: Optional[HistoryPromptTemplate] = None,
        rewrite_prompt: Optional[RewritePromptTemplate] = None,
        generate_prompt: Optional[GenerateAnswerPromptTemplate] = None,
    ):
        super().__init__(model, embeddings, vector_store)
        self.chat_history = chat_history
        
        # Create async retriever
        async_retriever = VectorStoreRetriever(vector_store=self.vector_store)
        self.retrieve_tool = create_retriever_tool(
            retriever=async_retriever,
            name="search_documents",
            description="Search through documents to find relevant information"
        )

        self.history_prompt = HistoryPromptTemplate().get_prompt_template()
        self.rewrite_prompt = RewritePromptTemplate().get_prompt_template()
        self.generate_prompt = GenerateAnswerPromptTemplate().get_prompt_template()
        self.direct_response_prompt = DirectResponsePromptTemplate().get_prompt_template()
        self.grader_prompt = GraderPromptTemplate().get_prompt_template()
        self.max_retrieval_attempts = 3
        self.retrieval_attempts = 0
        self.graph = self._setup_workflow()
        self.new_chats = []
        
    def _update_new_chats(self, chat: HumanMessage or AIMessage):
        """Update the chat history."""
        self.new_chats.append(chat)
        
    async def _history(self, state):
        """Process chat history for context."""
        chain = self.history_prompt | self.llm
        messages = state["messages"]
        question = messages[0].content
        assert question == messages[-1].content
        response = await chain.ainvoke({"chat_history": self.chat_history, "question": question})
        self.chat_history.add_user_message(response.content)
        return {"messages": [response]}

    async def _grade_documents(self, state) -> Literal["rewrite", "generate", "direct_response"]:
        """Grade document relevance."""
        # Data model
        self.retrieval_attempts += 1
                
        class grade(BaseModel):
            """Binary score for relevance check."""
            binary_score: str = Field(description="Relevance score 'yes' or 'no'")

        # Invoke chain
        llm_with_tool = self.llm.with_structured_output(grade)
        chain = self.grader_prompt | llm_with_tool
        messages = state["messages"]
        last_message = messages[-1]
        question = messages[1].content
        docs = last_message.content
        scored_result = await chain.ainvoke({"question": question, "context": docs})
        score = scored_result.binary_score
        if score == "yes":
            return "generate"
        elif score == "no" and self.retrieval_attempts + 1 == self.max_retrieval_attempts:
            return "direct_response"
        else:
            return "rewrite"

    async def _agent(self, state: MessagesState):
        """Decide whether to retrieve or respond."""
        llm_with_tools = self.llm.bind_tools([self.retrieve_tool])
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    async def _rewrite(self, state):
        """Rewrite the query for better retrieval."""
        messages = state["messages"]
        question = messages[1].content
        chain = self.rewrite_prompt | self.llm
        response = await chain.ainvoke(question)
        return {"messages": [response]}

    async def _generate(self, state):
        """Generate answer."""
        messages = state["messages"]
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt --> adds former messages from graph
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        question = messages[1].content 
        gen_chain = self.generate_prompt | self.llm | StrOutputParser()

        response = await gen_chain.ainvoke({"context": docs_content, "question": question})
        return {"messages": [response]}
    
    async def _direct_response(self, state):
        """Generate a highly constrained response when not using tools."""        
        messages = state["messages"]
        question = messages[0].content
        
        chain = self.direct_response_prompt | self.llm | StrOutputParser()
        response = await chain.ainvoke({"question": question})
        
        return {"messages": [response]}

    def _setup_workflow(self) -> StateGraph:
        """Set up the chat workflow."""
        workflow = StateGraph(MessagesState)
        tools = ToolNode([self.retrieve_tool])

        # Add nodes
        workflow.add_node("history", self._history)
        workflow.add_node("agent", self._agent)  # agent
        workflow.add_node("retrieve", tools)  # retrieval
        workflow.add_node("rewrite", self._rewrite) # Re-writing the question
        workflow.add_node("generate", self._generate) # generate answer
        workflow.add_node("direct_response", self._direct_response) # direct response for irrelevant question

        workflow.add_edge(START, "history")
        workflow.add_edge("history", "agent")

        # Decide whether to retrieve
        workflow.add_conditional_edges(
            "agent",
            # Assess agent decision
            tools_condition,
            {
                # Translate the condition outputs to nodes in our graph
                "tools": "retrieve",
                END: "direct_response",
            },
        )
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_documents,
            {
                "rewrite": "rewrite",
                "generate": "generate",
                "direct_response": "direct_response",
            }
        )

        workflow.add_edge("rewrite", "agent")
        workflow.add_edge("generate", END)
        workflow.add_edge("direct_response", END)

        return workflow.compile()
    
    
    def get_compiled_graph(self):
        return self.graph
    
    def get_new_chats(self):
        return self.new_chats
    
    def display(self):
        """Override string representation to display graph visualization."""
        return Image(self.get_compiled_graph().get_graph(xray=True).draw_mermaid_png())

    def process_query_test(self, query: str):
        """Synchronous query processing - mainly for testing."""
        self.retrieval_attempts = 0
        inputs = {"messages": [HumanMessage(content=query)]}
        for msg, metadata in self.graph.stream(inputs, stream_mode="messages"):
            if (msg.content and metadata["langgraph_node"] == "generate"):
                print(msg.content, flush=True)

    async def process_query_async(self, query: str) -> AsyncGenerator[str, None]:
        """Asynchronously process a query and stream responses."""
        self.retrieval_attempts = 0
        self._update_new_chats(HumanMessage(content=query))
        final_response = ""
        inputs = {"messages": [HumanMessage(content=query)]}
        async for msg, metadata in self.graph.astream(inputs, stream_mode="messages"):
            if msg.content and metadata["langgraph_node"] == "generate" or metadata["langgraph_node"] == "direct_response":
                yield msg.content
                final_response += msg.content
                await asyncio.sleep(0.1)
        final_response = AIMessage(content=final_response)
        self._update_new_chats(final_response)
        self.chat_history.add_ai_message(final_response)
