from django.urls import path
from . import views
from django.urls import include

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_document, name='upload_document'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('search/', views.search_page, name='search_page'),
    
    # API
    path('api/v1/', include('rag_search.api.urls')),
]
