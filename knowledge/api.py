from rest_framework import viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import Article, Section, Attachment, UserProfile
from .serializers import ArticleSerializer, SectionSerializer, AttachmentSerializer, UserProfileSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(status='published').select_related('author', 'section').prefetch_related('attachments')
    serializer_class = ArticleSerializer

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().prefetch_related('article_set')
    serializer_class = SectionSerializer

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().select_related('user')
    serializer_class = UserProfileSerializer

@api_view(['GET'])
def search_articles(request):
    query = request.GET.get('q', '')
    if query:
        articles = Article.objects.filter(
            Q(status='published') & 
            (Q(title__icontains=query) | Q(content__icontains=query) | Q(summary__icontains=query))
        ).select_related('author', 'section').prefetch_related('attachments')
    else:
        articles = Article.objects.filter(status='published').select_related('author', 'section').prefetch_related('attachments')
    
    serializer = ArticleSerializer(articles, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_section_articles(request, section_id):
    articles = Article.objects.filter(
        section_id=section_id, 
        status='published'
    ).select_related('author', 'section').prefetch_related('attachments')
    
    serializer = ArticleSerializer(articles, many=True)
    return Response(serializer.data)