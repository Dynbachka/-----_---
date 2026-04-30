from django.urls import path
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api
from django.urls import path
from .views import RegisterUserView, CustomLoginView
from django.contrib.auth.views import LogoutView
from .views import ProfileView


app_name = 'knowledge'

router = DefaultRouter()
router.register(r'api/articles', api.ArticleViewSet)
router.register(r'api/sections', api.SectionViewSet)
router.register(r'api/attachments', api.AttachmentViewSet)
router.register(r'api/userprofiles', api.UserProfileViewSet)

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    path('sections/', views.all_sections, name='all_sections'),
    # Разделы
    path('section/<int:section_id>/', views.section_detail, name='section_detail'),

    # Статьи
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),

    # Создание и редактирование статей
    path('article/create/', views.create_article, name='create_article'),
    path('article/create/<int:section_id>/', views.create_article, name='create_article_in_section'),
    path('article/edit/<int:article_id>/', views.edit_article, name='edit_article'),

    # Работа с файлами
    path('attachment/download/<int:attachment_id>/', views.download_attachment, name='download_attachment'),
    path('attachment/view/<int:attachment_id>/', views.view_attachment, name='view_attachment'),

    # Поиск
    path('ajax/search/', views.search_autocomplete, name='search_autocomplete'),
    path('search/', views.search, name='search'),

    # Теги
    path('tag/<str:tag_name>/', views.articles_by_tag, name='articles_by_tag'),
    path('tags/', views.tag_cloud, name='tag_cloud'),
    
    # Файлы
    path('attachment/<int:attachment_id>/download/', views.download_attachment, name='download_attachment'),
    path('attachment/<int:attachment_id>/view/', views.view_attachment, name='view_attachment'),
    
    # Авторизация 
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='knowledge:home'), name='logout'),
    path('register/', RegisterUserView.as_view(), name='register'),
    
    # Авторизация 
    path('profile/', ProfileView.as_view(), name='profile'),
]
    ##
    ##   дял апи
    ##
    
    
    # path('', include(router.urls)),
    # path('api/search/', api.search_articles, name='api_search'),
    # path('api/articles/tag/<str:tag_name>/', api.articles_by_tag, name='api_articles_by_tag'),
    
    


# urlpatterns = [
#     path('', include(router.urls)),
#     path('api/search/', api.search_articles, name='api_search'),
#     path('api/sections/<int:section_id>/articles/', api.get_section_articles, name='api_section_articles'),
    
#     # Твои существующие URLs
#     path('', views.home, name='home'),
#     path('section/<int:section_id>/', views.section_detail, name='section_detail'),
#     path('article/<int:article_id>/', views.article_detail, name='article_detail'),
#     path('attachment/download/<int:attachment_id>/', views.download_attachment, name='download_attachment'),
#     path('attachment/view/<int:attachment_id>/', views.view_attachment, name='view_attachment'),
#     path('search/', views.search, name='search'),
#     path('article/create/', views.create_article, name='create_article'),
#     path('article/create/<int:section_id>/', views.create_article, name='create_article_in_section'),
#     path('article/edit/<int:article_id>/', views.edit_article, name='edit_article'),
# ]