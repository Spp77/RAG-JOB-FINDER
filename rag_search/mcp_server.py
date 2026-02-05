
import os
import sys
import django
import logging
from typing import List, Dict, Any

# Configure Django environment for standalone script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp.server.fastmcp import FastMCP
from rag_search.services.rag_service import RAGService
from rag_search.models import Document
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobFinderMCP")

# Initialize RAG Service
rag_service = RAGService.get_instance()

# Initialize FastMCP
mcp = FastMCP("JobFinderMCP")

@mcp.tool()
def search_jobs(query: str) -> str:
    """
    Search for jobs or resumes using semantic search.
    Provides relevant context from indexed documents.
    """
    logger.info(f"MCP Search Query: {query}")
    result = rag_service.search(query)
    return result.get("result", "No relevant information found.")

@mcp.tool()
def list_available_documents() -> str:
    """
    List all documents (resumes, job descriptions) currently in the system.
    """
    docs = Document.objects.all()
    if not docs.exists():
        return "No documents found in the database."
    
    doc_list = "\n".join([f"- {d.title} (Uploaded: {d.uploaded_at.strftime('%Y-%m-%d')})" for d in docs])
    return f"Indexed Documents:\n{doc_list}"

@mcp.tool()
def add_job_description(title: str, content: str) -> str:
    """
    Add a new job description or career information to the RAG system.
    This creates a new document which will be indexed for future searches.
    """
    try:
        # We need a user to assign as 'uploaded_by'
        # For MCP, we'll use the first superuser as a fallback or a dedicated 'mcp_user'
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            return "Error: No admin user found to associate with this document."

        # Create the file in the data directory
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '.', '_')]).rstrip()
        filename = f"{safe_title.replace(' ', '_')}.txt"
        
        # We save it to the Document model
        doc = Document(
            title=title,
            uploaded_by=admin_user
        )
        doc.file.save(filename, ContentFile(content))
        doc.save()

        # Reload RAG DB to index the new document
        rag_service.reload_db()
        
        return f"Successfully added and indexed document: {title}"
    except Exception as e:
        logger.error(f"Failed to add document via MCP: {e}")
        return f"Error adding document: {str(e)}"

if __name__ == "__main__":
    # When run directly, start the MCP server (stdio transport)
    mcp.run()
