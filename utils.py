from typing import Optional, List, Dict, Any
import os
import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_teddynote import logging
from langchain_teddynote.prompts import load_prompt

# Constants
CACHE_DIR = ".cache"
FILES_DIR = os.path.join(CACHE_DIR, "files")
MANUAL_DIR = os.path.join(FILES_DIR, "manual_files")
PROBLEM_DIR = os.path.join(FILES_DIR, "problem_files")
PAPER_DIR = os.path.join(FILES_DIR, "paper_files")
EMBEDDINGS_DIR = os.path.join(CACHE_DIR, "embeddings")

# Directory initialization
def initialize_directories():
    for dir_path in [CACHE_DIR, FILES_DIR, MANUAL_DIR, PROBLEM_DIR, PAPER_DIR, EMBEDDINGS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

class DocumentLoader:
    @staticmethod
    @st.cache_resource(show_spinner=False, ttl=3600)
    def load_documents(directory: str, file_type: str = "pdf") -> Optional[object]:
        try:
            documents = []
            if not os.path.exists(directory):
                raise Exception(f"Directory not found: {directory}")
            
            files = [f for f in os.listdir(directory) if f.endswith(f'.{file_type}')]
            if not files:
                raise Exception(f"No {file_type} files found in {directory}")
            
            for filename in files:
                file_path = os.path.join(directory, filename)
                # st.info(f"Loading file: {filename}")
                try:
                    loader = PDFPlumberLoader(file_path)
                    documents.extend(loader.load())
                except Exception as e:
                    st.warning(f"Failed to load {filename}: {str(e)}")
                    continue
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=50,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            split_documents = text_splitter.split_documents(documents)
            
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)
            
            return vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5}
            )
        
        except Exception as e:
            st.error(f"Error in document loading: {str(e)}")
            return None

class ChatManager:
    @staticmethod
    def initialize_session_state(page_name: str):
        messages_key = f"{page_name}_messages"
        if messages_key not in st.session_state:
            st.session_state[messages_key] = []
        if "is_loading" not in st.session_state:
            st.session_state["is_loading"] = False
    
    @staticmethod
    def get_messages_key(page_name: str) -> str:
        return f"{page_name}_messages"
    
    @staticmethod
    def print_messages(page_name: str):
        messages_key = ChatManager.get_messages_key(page_name)
        for chat_message in st.session_state[messages_key]:
            st.chat_message(chat_message.role).write(chat_message.content)
    
    @staticmethod
    def add_message(page_name: str, role: str, message: str):
        messages_key = ChatManager.get_messages_key(page_name)
        st.session_state[messages_key].append(ChatMessage(role=role, content=message))
    
    @staticmethod
    def clear_messages(page_name: str):
        messages_key = ChatManager.get_messages_key(page_name)
        st.session_state[messages_key] = []

class ChainManager:
    @staticmethod
    def create_chain(retriever: Any, model_name: str = "gpt-4o") -> Any:
        prompt = load_prompt("prompts/pdf-rag.yaml", encoding="utf-8")
        llm = ChatOpenAI(model_name=model_name, temperature=0)
        
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain
