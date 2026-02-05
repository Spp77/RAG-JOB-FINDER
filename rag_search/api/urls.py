from django.urls import path
from rag_search.api import views
from rag_search.mcp_server import MCPEndpoint

urlpatterns = [
    path('search/', views.SearchAPIView.as_view(), name='api_search'),
    path('reload/', views.ReloadDBReview.as_view(), name='api_reload'),
    
    # MCP Endpoint (SSE)
    path('mcp/sse/', MCPEndpoint.as_view(), name='mcp_sse'),
]
