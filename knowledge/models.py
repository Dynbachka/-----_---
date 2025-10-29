from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField
from taggit.managers import TaggableManager

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('author', 'Автор'),
        ('user', 'Пользователь'),
    ]
    
    role_name = models.CharField(
        max_length=50, 
        unique=True,
        choices=ROLE_CHOICES,
        verbose_name='Название роли'
    )
    description = models.TextField(blank=True, verbose_name='Описание роли')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'

    def __str__(self):
        return self.get_role_name_display()

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    roles = models.ManyToManyField(
        UserRole, 
        blank=True,
        verbose_name='Роли'
    )
    bio = models.TextField(blank=True, verbose_name='Биография')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.username}"
    
    def has_role(self, role_name):
        """Проверяет, есть ли у пользователя указанная роль"""
        return self.roles.filter(role_name=role_name).exists()

    def has_role(self, role_name):
        return self.roles.filter(role_name=role_name).exists()

class Section(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название раздела')
    description = models.TextField(blank=True, verbose_name='Описание раздела')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский раздел'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_sections',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order_index = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    full_path = models.CharField(max_length=1000, blank=True, verbose_name='Полный путь')

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'
        ordering = ['order_index', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.parent:
            self.full_path = f"{self.parent.full_path} > {self.title}"
        else:
            self.full_path = self.title
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('section_detail', kwargs={'pk': self.pk})

    def get_articles_count(self):
        return self.articles.filter(status='published').count()

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
    ]

    title = models.CharField(max_length=500, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    summary = models.TextField(blank=True, verbose_name='Краткое описание')
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Раздел'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Автор'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус'
    )
    view_count = models.IntegerField(default=0, verbose_name='Количество просмотров')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации'
    )
    version = models.IntegerField(default=1, verbose_name='Версия')
    search_vector = SearchVectorField(null=True, verbose_name='Вектор поиска')
    
    # Менеджер тегов
    tags = TaggableManager(blank=True, verbose_name='Теги')

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['section', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'pk': self.pk})

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class Attachment(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Статья'
    )
    file_name = models.CharField(max_length=500, verbose_name='Имя файла')
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        verbose_name='Файл'
    )
    file_size = models.IntegerField(blank=True, null=True, verbose_name='Размер файла')
    file_type = models.CharField(max_length=100, blank=True, verbose_name='Тип файла')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Загрузил',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Прикрепленный файл'
        verbose_name_plural = 'Прикрепленные файлы'

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)

    def get_file_url(self):
        """Возвращает URL для скачивания файла"""
        return self.file.url

    def get_file_icon(self):
        """Возвращает иконку в зависимости от типа файла"""
        file_type = self.file_type.lower()
        
        if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
            return '🖼️'
        elif file_type in ['pdf']:
            return '📄'
        elif file_type in ['doc', 'docx']:
            return '📝'
        elif file_type in ['xls', 'xlsx']:
            return '📊'
        elif file_type in ['zip', 'rar', '7z']:
            return '📦'
        elif file_type in ['mp4', 'avi', 'mov', 'mkv']:
            return '🎬'
        elif file_type in ['mp3', 'wav', 'ogg']:
            return '🎵'
        else:
            return '📎'

    def is_image(self):
        """Проверяет, является ли файл изображением"""
        image_types = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
        return self.file_type.lower() in image_types

    def is_previewable(self):
        """Можно ли показать превью файла"""
        return self.is_image() or self.file_type.lower() == 'pdf'
    
class ArticleHistory(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Статья'
    )
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    version = models.IntegerField(verbose_name='Версия')
    modified_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Кто изменил'
    )
    modified_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')
    change_reason = models.TextField(blank=True, verbose_name='Причина изменения')

    class Meta:
        verbose_name = 'История статьи'
        verbose_name_plural = 'История статей'
        ordering = ['-modified_at']

    def __str__(self):
        return f"{self.article.title} - v{self.version}"
    
    @classmethod
    def get_tree_structure(cls):
        """Возвращает древовидную структуру разделов"""
        sections = cls.objects.filter(is_active=True).order_by('parent__title', 'title')
        tree = {}
    
        for section in sections:
            if section.parent is None:
                # Корневой раздел
                if section.id not in tree:
                    tree[section.id] = {
                        'section': section,
                        'children': []
                    }
            else:
                # Подраздел
                if section.parent.id not in tree:
                    tree[section.parent.id] = {
                        'section': section.parent,
                        'children': []
                    }
                tree[section.parent.id]['children'].append(section)
    
        return tree