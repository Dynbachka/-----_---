from django import forms
from .models import Article, Section, Attachment
from taggit.forms import TagField
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from .models import UserProfile


# Кастомный виджет для загрузки нескольких файлов
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ArticleForm(forms.ModelForm):
    """Форма для создания и редактирования статей"""
    
    tags = TagField(
        required=False,
        label='Теги',
        help_text='Введите теги через запятую'
    )
    
    # Поле для загрузки нескольких файлов
    attachments = MultipleFileField(
        required=False,
        label='Прикрепить файлы',
        help_text='Вы можете выбрать несколько файлов одновременно'
    )
    
    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'section', 'status', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Введите заголовок статьи',
                'required': True
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание статьи (необязательно)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Содержание статьи',
                'required': True
            }),
            'section': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
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
            
            # Обрабатываем загруженные файлы
            self._save_attachments(article)
        
        return article
    
    def _save_attachments(self, article):
        """Сохраняем загруженные файлы"""
        files = self.files.getlist('attachments')
        for file in files:
            if file:
                # Получаем расширение файла
                file_extension = file.name.split('.')[-1].lower() if '.' in file.name else 'unknown'
                
                attachment = Attachment(
                    article=article,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    file_type=file_extension,
                    uploaded_by=article.author
                )
                attachment.save()


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
                version=original.version,
                modified_by=modified_by,
                change_reason=change_reason or "Редактирование статьи"
            )
            article.version += 1
        
        if commit:
            article.save()
            self.save_m2m()  # Сохраняем теги
            
            # Обрабатываем загруженные файлы
            self._save_attachments(article)
        
        return article
    
    def _save_attachments(self, article):
        """Сохраняем загруженные файлы"""
        files = self.files.getlist('attachments')
        for file in files:
            if file:
                # Получаем расширение файла
                file_extension = file.name.split('.')[-1].lower() if '.' in file.name else 'unknown'
                
                attachment = Attachment(
                    article=article,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    file_type=file_extension,
                    uploaded_by=article.author
                )
                attachment.save()
                
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-control ко всем полям для красивого отображения
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-control ко всем полям для красивого отображения
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя', max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Фамилия', max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'bio': 'О себе',
            'avatar': 'Аватар',
        }

    def __init__(self, *args, **kwargs):
        # Передаём instance пользователя отдельно
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save()
        if commit:
            profile.save()
        return profile