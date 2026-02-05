from django.contrib import admin
from .models import Document, SearchHistory

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'uploaded_at')
    search_fields = ('title',)
    list_filter = ('uploaded_at', 'uploaded_by')

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'created_at')
    search_fields = ('query', 'user__username')
    list_filter = ('created_at',)
