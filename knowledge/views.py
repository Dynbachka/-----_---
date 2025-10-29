from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.postgres.search import SearchVector
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Section, Article, UserProfile, Attachment  # ДОБАВЬ Attachment
from .forms import ArticleCreateForm, ArticleEditForm
from django.core.paginator import Paginator

def home(request):
    """Главная страница с разделами и популярными статьями"""
    # Получаем корневые разделы (без родителей)
    root_sections = Section.objects.filter(parent__isnull=True, is_active=True)
    
    # Получаем последние опубликованные статьи
    recent_articles = Article.objects.filter(
        status='published'
    ).select_related('section', 'author').order_by('-created_at')[:10]
    
    # Получаем популярные статьи (по просмотрам)
    popular_articles = Article.objects.filter(
        status='published'
    ).select_related('section', 'author').order_by('-view_count')[:5]
    
    context = {
        'root_sections': root_sections,
        'recent_articles': recent_articles,
        'popular_articles': popular_articles,
    }
    return render(request, 'knowledge/home.html', context)

def section_detail(request, section_id):
    """Детальная страница раздела"""
    section = get_object_or_404(Section, id=section_id, is_active=True)
    
    # Получаем подразделы
    subsections = Section.objects.filter(parent=section, is_active=True)
    
    # Получаем статьи раздела
    articles = Article.objects.filter(
        section=section, 
        status='published'
    ).select_related('author')
    
    # Получаем путь к разделу (иерархия)
    breadcrumbs = []
    current_section = section
    while current_section:
        breadcrumbs.insert(0, current_section)
        current_section = current_section.parent
    
    context = {
        'section': section,
        'subsections': subsections,
        'articles': articles,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'knowledge/section_detail.html', context)

def article_detail(request, article_id):
    """Детальная страница статьи"""
    article = get_object_or_404(Article, id=article_id)
    
    # Увеличиваем счетчик просмотров только для опубликованных статей
    if article.status == 'published':
        article.increment_view_count()
    
    # Получаем связанные статьи (из того же раздела)
    related_articles = Article.objects.filter(
        section=article.section,
        status='published'
    ).exclude(id=article.id).select_related('author')[:5]
    
    # Получаем путь к статье
    breadcrumbs = []
    current_section = article.section
    while current_section:
        breadcrumbs.insert(0, current_section)
        current_section = current_section.parent
    
    context = {
        'article': article,
        'related_articles': related_articles,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'knowledge/article_detail.html', context)

def search(request):
    """Полнотекстовый поиск по статьям"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        # Используем полнотекстовый поиск PostgreSQL
        results = Article.objects.filter(status='published').annotate(
            search=SearchVector('title', 'content', 'summary')
        ).filter(search=query).select_related('section', 'author')
    
    # Пагинация
    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'results': page_obj,
        'results_count': len(results),
    }
    return render(request, 'knowledge/search.html', context)

def articles_by_tag(request, tag_name):
    """Статьи по тегу"""
    articles = Article.objects.filter(
        tags__name=tag_name,
        status='published'
    ).select_related('section', 'author')
    
    context = {
        'tag_name': tag_name,
        'articles': articles,
    }
    return render(request, 'knowledge/articles_by_tag.html', context)

@login_required
def create_article(request, section_id=None):
    """Создание новой статьи"""
    if not request.user.profile.has_role('author') and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для создания статей')
        return redirect('knowledge:home')  # ИСПРАВЛЕНО
    
    section = None
    if section_id:
        section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST)
        if form.is_valid():
            article = form.save(author=request.user)
            messages.success(request, f'Статья "{article.title}" успешно создана!')
            return redirect('knowledge:article_detail', article_id=article.id)  # ИСПРАВЛЕНО
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        initial = {}
        if section:
            initial['section'] = section
        form = ArticleCreateForm(initial=initial)
    
    all_sections = Section.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'section': section,
        'all_sections': all_sections,
    }
    return render(request, 'knowledge/create_article.html', context)

@login_required
def edit_article(request, article_id):
    """Редактирование статьи"""
    article = get_object_or_404(Article, id=article_id)
    
    # Проверяем права
    if not (request.user == article.author or 
            request.user.profile.has_role('author') or 
            request.user.is_staff):
        messages.error(request, 'У вас нет прав для редактирования этой статьи')
        return redirect('knowledge:article_detail', article_id=article.id)  # ИСПРАВЛЕНО
    
    if request.method == 'POST':
        form = ArticleEditForm(request.POST, instance=article)
        if form.is_valid():
            change_reason = form.cleaned_data.get('change_reason')
            article = form.save(modified_by=request.user, change_reason=change_reason)
            messages.success(request, f'Статья "{article.title}" успешно обновлена!')
            return redirect('knowledge:article_detail', article_id=article.id)  # ИСПРАВЛЕНО
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = ArticleEditForm(instance=article)
    
    all_sections = Section.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'article': article,
        'all_sections': all_sections,
    }
    return render(request, 'knowledge/edit_article.html', context)

def tag_cloud(request):
    """Облако тегов"""
    from taggit.models import Tag
    tags = Tag.objects.all()
    
    context = {
        'tags': tags,
    }
    return render(request, 'knowledge/tag_cloud.html', context)

def download_attachment(request, attachment_id):
    """Скачивание прикрепленного файла"""
    attachment = get_object_or_404(Attachment, id=attachment_id)
    
    # Проверяем доступ к статье
    article = attachment.article
    if article.status != 'published' and not request.user.is_authenticated:
        raise Http404("Файл не найден")
    
    file_path = attachment.file.path
    file_name = attachment.file_name
    
    # Для безопасной отдачи файла
    response = FileResponse(attachment.file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    response['Content-Type'] = 'application/octet-stream'
    
    return response

def view_attachment(request, attachment_id):
    """Просмотр файла (для изображений и PDF)"""
    attachment = get_object_or_404(Attachment, id=attachment_id)
    
    # Проверяем доступ к статье
    article = attachment.article
    if article.status != 'published' and not request.user.is_authenticated:
        raise Http404("Файл не найден")
    
    if attachment.is_image():
        # Для изображений показываем прямо в браузере
        response = FileResponse(attachment.file.open('rb'))
        response['Content-Disposition'] = f'inline; filename="{attachment.file_name}"'
        response['Content-Type'] = f'image/{attachment.file_type}'
        return response
    else:
        # Для остальных файлов - скачивание
        return download_attachment(request, attachment_id)