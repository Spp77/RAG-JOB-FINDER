
import os
import shutil
import logging
import requests
import time
from typing import List, Dict, Optional, Any

from django.conf import settings
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import LLM

# Configure logging
logger = logging.getLogger(__name__)

class SimpleHuggingFaceLLM(LLM):
    """
    Custom LLM wrapper to call Hugging Face Inference API directly via requests.
    Bypasses huggingface_hub complex provider resolution and library bugs.
    """
    repo_id: str
    api_token: str
    temperature: float = 0.5
    max_new_tokens: int = 512

    @property
    def _llm_type(self) -> str:
        return "custom_huggingface"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        api_url = f"https://api-inference.huggingface.co/models/{self.repo_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_new_tokens,
                "temperature": self.temperature,
                "return_full_text": False
            }
        }

        # Simple retry logic
        for _ in range(3):
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                    elif isinstance(result, dict) and "generated_text" in result:
                        return result.get("generated_text", "").strip()
                    return str(result).strip()
                elif response.status_code == 503:
                    # Model loading
                    logger.info("Model loading on Hugging Face, waiting 15s...")
                    time.sleep(15)
                    continue
                else:
                    logger.error(f"HF API Error: {response.status_code} - {response.text}")
                    raise ValueError(f"Hugging Face API Error: {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"Connection error to HF: {e}. Retrying...")
                time.sleep(5)
                continue
        
        raise ValueError("Failed to get response from Hugging Face API after 3 retries.")

class RAGService:
    """
    Job Finder RAG Service (Optimized).
    Handles Vector DB management and semantic search for job/resume matching.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'RAGService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        try:
            # Initialize Embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=getattr(settings, 'RAG_EMBEDDING_MODEL', "sentence-transformers/all-MiniLM-L6-v2")
            )
            
            # Paths
            self.vector_db_path = os.path.join(settings.BASE_DIR, "vector_db")
            self.search_paths = [
                os.path.join(settings.MEDIA_ROOT, "documents"), 
                os.path.join(settings.BASE_DIR, "data"),        
            ]
            
            # Create data dir if not exists
            os.makedirs(os.path.join(settings.BASE_DIR, "data"), exist_ok=True)
            
            # Initialize DB
            self.vectordb = self._initialize_vector_db()
            
        except Exception as e:
            logger.critical(f"RAGService Initialization Error: {e}")
            raise

    def _initialize_vector_db(self) -> Optional[Chroma]:
        if not os.path.exists(self.vector_db_path) or not os.listdir(self.vector_db_path):
            return self._build_db()
        else:
            logger.info("Loading existing Job Finder vector database...")
            try:
                return Chroma(
                    persist_directory=self.vector_db_path,
                    embedding_function=self.embeddings
                )
            except Exception as e:
                logger.error(f"Error loading Chroma DB: {e}. Attempting rebuild...")
                return self._build_db()

    def _build_db(self) -> Optional[Chroma]:
        logger.info("Building fresh Vector DB for Job Finder...")
        documents = []
        
        for path in self.search_paths:
            if not os.path.exists(path):
                continue
            
            # Load TXT
            try:
                txt_loader = DirectoryLoader(path, glob="**/*.txt", loader_cls=TextLoader)
                documents.extend(txt_loader.load())
            except Exception as e:
                logger.error(f"Error loading TXT from {path}: {e}")
                
            # Load PDF
            try:
                pdf_loader = DirectoryLoader(path, glob="**/*.pdf", loader_cls=PyPDFLoader)
                documents.extend(pdf_loader.load())
            except Exception as e:
                logger.error(f"Error loading PDF from {path}: {e}")
        
        if not documents:
            logger.warning("No documents found to index.")
            return None

        # Optimization: Overlapping chunks for better context preservation
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        split_docs = splitter.split_documents(documents)

        try:
            vectordb = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=self.vector_db_path
            )
            logger.info(f"Successfully indexed {len(split_docs)} chunks from {len(documents)} documents.")
            return vectordb
        except Exception as e:
            logger.error(f"Vector DB Build Failed: {e}")
            return None

    def search(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for job search queries.
        """
        if not self.vectordb:
            self.vectordb = self._build_db()
            if not self.vectordb:
                return {
                    "result": "I don't have any job descriptions or resumes indexed yet. Please upload some documents so I can help you!", 
                    "source_documents": []
                }

        # 1. Retriever setup (Optimized for quality)
        retriever = self.vectordb.as_retriever(
            search_type="mmr", # Maximum Marginal Relevance for variety
            search_kwargs={"k": 5, "fetch_k": 20}
        )
        
        # 2. LLM Setup
        api_key = os.getenv("HUGGING_FACE_HUB_TOKEN") or os.getenv("hugging_api")
        if not api_key:
             return {"result": "Configuration Error: Hugging Face API token missing in .env (expected HUGGING_FACE_HUB_TOKEN)", "source_documents": []}

        try:
            llm = SimpleHuggingFaceLLM(
                repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                api_token=api_key,
                temperature=0.2, 
                max_new_tokens=1024
            )
        except Exception as e:
            logger.error(f"LLM Init Error: {e}")
            return {"result": f"Model Initialization Error: {e}. Please check your API token and internet connection.", "source_documents": []}

        # 3. Enhanced Prompt for RAG-JOB-FINDER
        template = """[INST] You are a professional Career Assistant and Job Matcher. 
Use the following context (job descriptions, resumes, and career data) to answer the user's question.
If the context doesn't contain the answer, say that you don't have enough information in your current database to answer specifically, but offer general advice.

CONTEXT:
{context}

QUESTION:
{question}

Please provide a detailed, professional, and helpful response. If matching a job to a resume, highlight specific skills that match.
ANSWER: [/INST]"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        try:
            # Retrieve documents
            docs = retriever.invoke(query)
            if not docs:
                return {"result": "I couldn't find any specific matches in the indexed documents for your query.", "source_documents": []}
                
            context_text = "\n\n".join([f"--- Document: {d.metadata.get('source', 'Unknown')} ---\n{d.page_content}" for d in docs])
            
            # Execute Chain
            chain = (
                {"context": lambda x: context_text, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            response_text = chain.invoke(query)
            
            # Format source docs for transparency
            sources = []
            for d in docs:
                source_path = d.metadata.get('source', 'Unknown')
                sources.append({
                    "content": d.page_content[:400] + "...",
                    "metadata": d.metadata,
                    "source_name": os.path.basename(source_path) if source_path != 'Unknown' else 'Unknown'
                })
            
            return {
                "result": response_text,
                "source_documents": sources
            }
        except Exception as e:
            logger.error(f"RAG Search failed: {e}")
            import traceback
            traceback.print_exc()
            return {"result": f"The RAG engine encountered a processing error: {str(e)}", "source_documents": []}

    def reload_db(self):
        """Force a complete re-index of the system."""
        try:
            if os.path.exists(self.vector_db_path):
                # Chroma might have locks, so we try to close it if possible
                self.vectordb = None 
                import gc
                gc.collect()
                time.sleep(1) # Give it a second to release files
                shutil.rmtree(self.vector_db_path)
            
            self.vectordb = self._build_db()
            return True
        except Exception as e:
            logger.error(f"Reload DB Failed: {e}")
            return False
