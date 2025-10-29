from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserRole, Section, Article, Attachment, ArticleHistory
from taggit.models import Tag as TaggitTag, TaggedItem

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['role_name', 'description', 'created_at']
    list_filter = ['role_name']
    search_fields = ['role_name', 'description']

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    filter_horizontal = ['roles']

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles']
    list_filter = ['is_staff', 'is_superuser', 'is_active']

    def get_roles(self, obj):
        if hasattr(obj, 'profile'):
            return ", ".join([role.role_name for role in obj.profile.roles.all()])
        return "Нет ролей"
    get_roles.short_description = 'Роли'

# Отменяем регистрацию стандартного User и регистрируем наш кастомный
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'created_by', 'created_at', 'is_active', 'get_articles_count']
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['title', 'description', 'full_path']
    readonly_fields = ['full_path', 'created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'parent', 'is_active', 'order_index')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'full_path', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_articles_count(self, obj):
        return obj.articles.count()
    get_articles_count.short_description = 'Кол-во статей'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1
    fields = ['file_name', 'file', 'file_size', 'file_type', 'description']
    readonly_fields = ['file_size', 'file_type']

    def save_model(self, request, obj, form, change):
        # Устанавливаем uploaded_by автоматически
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

class ArticleHistoryInline(admin.TabularInline):
    model = ArticleHistory
    extra = 0
    readonly_fields = ['title', 'version', 'modified_by', 'modified_at', 'change_reason']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'author', 'status', 'view_count', 'created_at', 'published_at']
    list_filter = ['status', 'section', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'summary']
    readonly_fields = ['view_count', 'created_at', 'updated_at', 'version', 'search_vector']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'summary', 'section', 'author', 'tags')
        }),
        ('Публикация', {
            'fields': ('status', 'published_at')
        }),
        ('Статистика', {
            'fields': ('view_count', 'version'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'search_vector'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AttachmentInline, ArticleHistoryInline]
    filter_horizontal = []

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        
        # Сохраняем историю при изменении
        if change:
            original = Article.objects.get(pk=obj.pk)
            if original.title != obj.title or original.content != obj.content:
                ArticleHistory.objects.create(
                    article=obj,
                    title=original.title,
                    content=original.content,
                    version=obj.version,
                    modified_by=request.user,
                    change_reason=f"Автоматическое сохранение версии {obj.version}"
                )
                obj.version += 1
        
        super().save_model(request, obj, form, change)

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'article', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'article__title']
    readonly_fields = ['file_size', 'file_type', 'uploaded_at']

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ArticleHistory)
class ArticleHistoryAdmin(admin.ModelAdmin):
    list_display = ['article', 'version', 'modified_by', 'modified_at']
    list_filter = ['modified_at', 'version']
    search_fields = ['article__title', 'title', 'content']
    readonly_fields = ['article', 'title', 'content', 'version', 'modified_by', 'modified_at', 'change_reason']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Убираем регистрацию Tag из админки, так как он управляется через TaggableManager
# НЕ РЕГИСТРИРУЕМ Tag здесь, так как он уже зарегистрирован в taggit

# Настройка заголовков админки
admin.site.site_header = 'Панель управления базой знаний'
admin.site.site_title = 'База знаний'
admin.site.index_title = 'Управление контентом'