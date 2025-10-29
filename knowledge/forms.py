from django import forms
from .models import Article, Section
from taggit.forms import TagField

class ArticleForm(forms.ModelForm):
    """Форма для создания и редактирования статей"""
    tags = TagField(
        required=False,
        label='Теги',
        help_text='Введите теги через запятую'
    )
    
    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'section', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок статьи'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание статьи (необязательно)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Содержание статьи'
            }),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Заголовок',
            'summary': 'Краткое описание',
            'content': 'Содержание',
            'section': 'Раздел',
            'status': 'Статус',
        }

class ArticleCreateForm(ArticleForm):
    """Форма для создания статьи с автоматическим назначением автора"""
    
    def save(self, commit=True, author=None):
        article = super().save(commit=False)
        if author:
            article.author = author
        if commit:
            article.save()
            self.save_m2m()  # Сохраняем теги
        return article

class ArticleEditForm(ArticleForm):
    """Форма для редактирования статьи с историей изменений"""
    change_reason = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Опишите причину изменений (для истории версий)'
        }),
        label='Причина изменения'
    )
    
    def save(self, commit=True, modified_by=None, change_reason=None):
        article = super().save(commit=False)
        
        # Сохраняем историю если есть изменения в содержании
        if article.pk and (self.has_changed() and modified_by):
            from .models import ArticleHistory
            original = Article.objects.get(pk=article.pk)
            
            ArticleHistory.objects.create(
                article=article,
                title=original.title,
                content=original.content,
                version=article.version,
                modified_by=modified_by,
                change_reason=change_reason or "Редактирование статьи"
            )
            article.version += 1
        
        if commit:
            article.save()
            self.save_m2m()  # Сохраняем теги
        
        return article