#!/usr/bin/env python3

# imports
from constants import TEMPLATE
import streamlit as st, logging
from langchain_ollama.llms import OllamaLLM
from typing import List, Optional, Dict, Any
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



class WebCrawlerChatbot:
    """
    Web crawler chatbot class
    """
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.embeddings = OllamaEmbeddings(model=model_name)
        self.vector_store = InMemoryVectorStore(self.embeddings)
        self.model = OllamaLLM(model=model_name)
        self.prompt = ChatPromptTemplate.from_template(TEMPLATE)
        self.chain = self.prompt | self.model
        logger.info(f"Initialized WebCrawlerChatbot with model: {model_name}")
    
    def load_page(self, url: str) -> List[Any]:
        """
        Load content from a URL using selenium in unstructured format
        default formaters wont fetch all the elements from java/type-script
        hence, selenium is better to fetch all the elements
        """
        logger.info(f"Loading content from URL: {url}")
        loader = SeleniumURLLoader(urls=[url])
        return loader.load()
    
    def split_text(self, documents: List[Any]) -> List[Any]:
        """
        Split documents into manageable chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks")
        return chunks
    
    def index_docs(self, documents: List[Any]) -> None:
        """
        Add documents to the vector store (inmemory)
        """
        self.vector_store.add_documents(documents)
        logger.info(f"Indexed {len(documents)} documents")
    
    def retrieve_docs(self, query: str) -> List[Any]:
        results = self.vector_store.similarity_search(query)
        logger.info(f"Retrieved {len(results)} documents for query: {query}")
        return results
    
    def answer_question(self, question: str, context: str) -> str:
        """
        Generate an answer based on the question and context
        """
        logger.info(f"Generating answer for question: {question}")
        return self.chain.invoke({"question": question, "context": context})
    
    def process_url(self, url: str) -> None:
        """
        Process a single URL - load, split, and index
        """
        logger.info(f"Processing URL: {url}")
        docs = self.load_page(url)
        chunks = self.split_text(docs)
        self.index_docs(chunks)
        logger.info(f"Completed processing URL: {url}")
    
    def process_urls(self, urls: List[str]) -> None:
        """
        Process multiple URLs
        """
        for url in urls:
            self.process_url(url)

def run_streamlit_app():
    chatbot = WebCrawlerChatbot()
    
    st.title("Web Crawler Chatbot")
    if "urls" not in st.session_state:
        st.session_state.urls = []
    if "indexed" not in st.session_state:
        st.session_state.indexed = False

    if len(st.session_state.urls) < 5 and not st.session_state.indexed:
        new_url = st.text_input("Enter URL (max 5):", key="new_url_input")
        if st.button("Add URL"):
            if new_url and new_url.strip():
                st.session_state.urls.append(new_url.strip())

    if st.session_state.urls:
        st.subheader("Sites Added:")
        for idx, url in enumerate(st.session_state.urls, start=1):
            st.write(f"{idx}. [{url}]({url})")

    if st.session_state.urls and not st.session_state.indexed:
        if st.button("Finalize Sites"):
            with st.spinner("Brewing up embeddings from your chosen sites..."):
                chatbot.process_urls(st.session_state.urls)
            st.session_state.indexed = True

    if st.session_state.indexed:
        st.success("All sites processed and indexed! Scroll down to chat.")
        st.subheader("Ask a Question")
        question = st.chat_input("Type your question here...")  
        if question:
            st.chat_message("user").write(question)
            retrieve_documents = chatbot.retrieve_docs(question)
            context = "\n\n".join([doc.page_content for doc in retrieve_documents])
            answer = chatbot.answer_question(question, context)
            st.chat_message("assistant").write(answer)

            sources_list = []
            for doc in retrieve_documents:
                source = doc.metadata.get("source", "title")
                sources_list.append(f"- {source}")
            if sources_list:
                st.markdown("**Information retrieved from:**")
                st.markdown("\n".join(sources_list))
    else:
        if not st.session_state.urls:
            st.info("Add a URL and then finalize them to unlock the magic of chat!")
        else:
            st.warning("Your sites are waiting to be indexed. Click 'Finalize Sites' above to continue!")

if __name__ == "__main__":
    run_streamlit_app()