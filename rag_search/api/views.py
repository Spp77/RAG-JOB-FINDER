from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rag_search.services.rag_service import RAGService
from .serializers import SearchQuerySerializer, SearchResponseSerializer, ReloadResponseSerializer

rag_service = RAGService.get_instance()

from rag_search.models import SearchHistory

class SearchAPIView(APIView):
    """
    API Endpoint for Semantic Search using RAG.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    serializer_class = SearchQuerySerializer

    @swagger_auto_schema(
        request_body=SearchQuerySerializer,
        responses={200: SearchResponseSerializer},
        operation_description="Search for jobs or documents using natural language."
    )
    def post(self, request):
        serializer = SearchQuerySerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            
            # Execute Search
            result = rag_service.search(query)
            
            # Save History (if user is authenticated)
            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=query,
                    result_summary=result.get('result', '')[:5000] # Truncate if too long
                )
            
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReloadDBReview(APIView):
    """
    Admin Endpoint to force reload the Vector Database.
    """
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    @swagger_auto_schema(
        responses={200: ReloadResponseSerializer},
        operation_description="Re-index all documents (Admin only)."
    )
    def post(self, request):
        try:
            rag_service.reload_db()
            return Response({"status": "success", "message": "Database reloaded successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
