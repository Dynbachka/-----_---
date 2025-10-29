from rest_framework import serializers
from .models import Article, Section, Attachment, UserProfile
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'bio', 'avatar']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file_name', 'file', 'file_size', 'file_type', 'description', 'uploaded_at']

class SectionSerializer(serializers.ModelSerializer):
    articles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ['id', 'title', 'description', 'parent', 'created_at', 'articles_count']
    
    def get_articles_count(self, obj):
        return obj.article_set.filter(status='published').count()

class ArticleSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    author = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'summary', 'section', 'author',
            'status', 'view_count', 'created_at', 'updated_at', 
            'published_at', 'attachments'
        ]