
import os
import django
import sys
import logging

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rag_search.services.rag_service import RAGService

# Configure logging to print to console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_rag():
    print("Initializing RAG Service...")
    try:
        service = RAGService.get_instance()
        print("RAG Service Initialized.")
    except Exception as e:
        print(f"FAILED to initialize RAG Service: {e}")
        import traceback
        traceback.print_exc()
        return

    query = "Find me a senior python developer job"
    print(f"\nPerforming Search for: '{query}'")
    
    try:
        result = service.search(query)
        print("\nSearch Result:")
        print(result)
    except Exception as e:
        print(f"\nFAILED during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rag()
