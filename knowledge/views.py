from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Section, Article, UserProfile, Attachment
from .forms import ArticleCreateForm, ArticleEditForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def is_admin_or_staff(user):
    """Проверка, является ли пользователь админом или сотрудником"""
    return user.is_staff or user.is_superuser


def home(request):
    """Главная страница с разделами и популярными статьями"""
    root_sections = Section.objects.filter(parent__isnull=True, is_active=True)
    
    recent_articles = Article.objects.filter(
        status='published'
    ).select_related('section', 'author').order_by('-created_at')[:10]
    
    popular_articles = Article.objects.filter(
        status='published'
    ).select_related('section', 'author').order_by('-view_count')[:5]
    
    context = {
        'root_sections': root_sections,
        'recent_articles': recent_articles,
        'popular_articles': popular_articles,
        'can_create_article': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'knowledge/home.html', context)


def section_detail(request, section_id):
    """Детальная страница раздела с пагинацией и сортировкой"""
    section = get_object_or_404(Section, id=section_id, is_active=True)
    
    subsections = Section.objects.filter(parent=section, is_active=True)
    
    articles = Article.objects.filter(
        section=section,
        status='published'
    ).select_related('author')
    
    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'popular':
        articles = articles.order_by('-view_count', '-created_at')
    elif sort == 'title':
        articles = articles.order_by('title')
    else:  # newest (по умолчанию)
        articles = articles.order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(articles, 10)  # 10 статей на странице
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Хлебные крошки
    breadcrumbs = []
    current_section = section
    while current_section:
        breadcrumbs.insert(0, current_section)
        current_section = current_section.parent
    
    context = {
        'section': section,
        'subsections': subsections,
        'articles': page_obj.object_list,  # Статьи на текущей странице
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'breadcrumbs': breadcrumbs,
        'can_create_article': request.user.is_staff or request.user.is_superuser,
        'current_sort': sort,
    }
    
    return render(request, 'knowledge/section_detail.html', context)


def article_detail(request, article_id):
    """Детальная страница статьи"""
    article = get_object_or_404(Article, id=article_id)
    
    if article.status == 'published':
        article.increment_view_count()
    
    related_articles = Article.objects.filter(
        section=article.section,
        status='published'
    ).exclude(id=article.id).select_related('author')[:5]
    
    breadcrumbs = []
    current_section = article.section
    while current_section:
        breadcrumbs.insert(0, current_section)
        current_section = current_section.parent
    
    can_edit = request.user.is_authenticated and (
        request.user == article.author or 
        request.user.is_staff or 
        request.user.is_superuser
    )
    
    context = {
        'article': article,
        'related_articles': related_articles,
        'breadcrumbs': breadcrumbs,
        'can_edit': can_edit,
    }
    
    return render(request, 'knowledge/article_detail.html', context)


def search(request):
    """Полнотекстовый поиск по статьям с пагинацией"""
    query = request.GET.get('q', '')
    results = None
    page_obj = None
    
    if query:
        # Полнотекстовый поиск
        results = Article.objects.filter(status='published').annotate(
            search=SearchVector('title', weight='A') + SearchVector('content', weight='B') + SearchVector('summary', weight='C')
        ).filter(search=query).select_related('section', 'author').order_by('-created_at')
        
        # Пагинация результатов
        paginator = Paginator(results, 20)  # 20 результатов на странице
        page_number = request.GET.get('page')
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'results': page_obj,
        'results_count': len(results) if results else 0,
    }
    
    return render(request, 'knowledge/search.html', context)


def articles_by_tag(request, tag_name):
    """Статьи по тегу с пагинацией"""
    articles = Article.objects.filter(
        tags__name=tag_name,
        status='published'
    ).select_related('section', 'author').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(articles, 15)  # 15 статей на странице
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'tag_name': tag_name,
        'articles': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'knowledge/articles_by_tag.html', context)


def tag_cloud(request):
    """Облако тегов - показывает популярные теги с фильтрацией и поиском"""
    from taggit.models import Tag
    
    # Базовый запрос
    tags = Tag.objects.annotate(
        num_times=Count('taggit_taggeditem_items')
    ).filter(num_times__gt=0).order_by('-num_times')
    
    # Поиск по названию тега
    search_query = request.GET.get('search', '').strip()
    if search_query:
        tags = tags.filter(name__icontains=search_query)
    
    # Сортировка
    sort = request.GET.get('sort', 'popular')
    if sort == 'name':
        tags = tags.order_by('name')
    elif sort == 'newest':
        tags = tags.order_by('-id')  # Новые теги в конце
    else:  # popular
        tags = tags.order_by('-num_times')
    
    # Пагинация
    paginator = Paginator(tags, 20)  # 20 тегов на странице
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Статистика
    all_tags = Tag.objects.annotate(num_times=Count('taggit_taggeditem_items')).filter(num_times__gt=0)
    total_tags = all_tags.count()
    total_uses = sum([tag.num_times for tag in all_tags])
    
    context = {
        'tags': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'current_sort': sort,
        'total_tags': total_tags,
        'total_uses': total_uses,
    }
    
    return render(request, 'knowledge/tag_cloud.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def create_article(request, section_id=None):
    """Создание новой статьи (только для админов)"""
    section = None
    if section_id:
        section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(author=request.user)
            messages.success(request, f'Статья "{article.title}" успешно создана!')
            return redirect('knowledge:article_detail', article_id=article.id)
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
        'page_title': 'Создание статьи',
    }
    
    return render(request, 'knowledge/create_article.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def edit_article(request, article_id):
    """Редактирование статьи (только для админов)"""
    article = get_object_or_404(Article, id=article_id)
    
    if request.method == 'POST':
        form = ArticleEditForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            change_reason = form.cleaned_data.get('change_reason')
            article = form.save(modified_by=request.user, change_reason=change_reason)
            messages.success(request, f'Статья "{article.title}" успешно обновлена!')
            return redirect('knowledge:article_detail', article_id=article.id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = ArticleEditForm(instance=article)
    
    all_sections = Section.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'article': article,
        'all_sections': all_sections,
        'page_title': f'Редактирование: {article.title}',
    }
    
    return render(request, 'knowledge/edit_article.html', context)


def download_attachment(request, attachment_id):
    """Скачивание прикрепленного файла"""
    attachment = get_object_or_404(Attachment, id=attachment_id)
    
    article = attachment.article
    if article.status != 'published' and not request.user.is_authenticated:
        raise Http404("Файл не найден")
    
    response = FileResponse(attachment.file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
    response['Content-Type'] = 'application/octet-stream'
    
    return response


def view_attachment(request, attachment_id):
    """Просмотр файла (для изображений и PDF)"""
    attachment = get_object_or_404(Attachment, id=attachment_id)
    
    article = attachment.article
    if article.status != 'published' and not request.user.is_authenticated:
        raise Http404("Файл не найден")
    
    if attachment.is_image():
        response = FileResponse(attachment.file.open('rb'))
        response['Content-Disposition'] = f'inline; filename="{attachment.file_name}"'
        response['Content-Type'] = f'image/{attachment.file_type}'
        return response
    else:
        return download_attachment(request, attachment_id)