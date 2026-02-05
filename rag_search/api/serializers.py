from rest_framework import serializers

class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True, max_length=1000)

class SourceDocumentSerializer(serializers.Serializer):
    content = serializers.CharField()
    metadata = serializers.DictField()
    source_name = serializers.CharField()

class SearchResponseSerializer(serializers.Serializer):
    result = serializers.CharField()
    source_documents = SourceDocumentSerializer(many=True)

class ReloadResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField(required=False)
