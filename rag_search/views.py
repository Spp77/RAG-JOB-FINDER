from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.rag_service import RAGService
from .models import Document
from .forms import DocumentForm

# RAG Service Instance
rag_service = RAGService.get_instance()

def home(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

from .models import Document, SearchHistory

from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
def dashboard(request):
    if is_admin(request.user):
        documents = Document.objects.all().order_by('-uploaded_at')
    else:
        documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    
    history = SearchHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'dashboard.html', {'documents': documents, 'history': history})

@login_required
@user_passes_test(is_admin)
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            
            # Trigger DB reload to index new file
            rag_service.reload_db()
            
            return redirect('dashboard')
    else:
        form = DocumentForm()
    return render(request, 'upload.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_document(request, doc_id):
    if is_admin(request.user):
        doc = get_object_or_404(Document, id=doc_id)
    else:
        doc = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)
    
    doc.delete() 
    rag_service.reload_db()
    return redirect('dashboard')

@login_required
def search_page(request):
    return render(request, 'search.html')

# API Views

@method_decorator(csrf_exempt, name='dispatch')
class SearchAPI(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        result = rag_service.search(query)
        return Response(result)

class ReloadDBAPI(APIView):
    def post(self, request):
        if not request.user.is_superuser:
             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        rag_service.reload_db()
        return Response({"status": "Database reloaded successfully"})
