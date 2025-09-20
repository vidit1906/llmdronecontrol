# vector_store.py
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os

class DroneCommandVectorStore:
    def __init__(self, persist_directory="./drone_commands_db"):
        # Initialize the embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.persist_directory = persist_directory
        
        # Initialize or load the vector store
        if os.path.exists(persist_directory):
            try:
                self.vector_store = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings
                )
                print(f"Loaded existing vector store from {persist_directory}")
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.vector_store = None
        else:
            self.vector_store = None
    
    def create_from_tello_commands(self, tello_txt_path="tello.txt"):
        """Create vector store from tello.txt file"""
        try:
            # Read the tello commands file
            with open(tello_txt_path, "r") as file:
                text = file.read()
            
            # Split the text into chunks
            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=100,
                chunk_overlap=20
            )
            
            chunks = text_splitter.split_text(text)
            
            # Create the vector store
            self.vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Persist to disk
            self.vector_store.persist()
            return len(chunks)
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return 0
    
    def similarity_search(self, query, k=5):
        """Search for similar commands based on user query"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call create_from_tello_commands first.")
        
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]