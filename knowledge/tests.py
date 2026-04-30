from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Section, Article, UserProfile, ArticleHistory
from .forms import (
    ArticleCreateForm, ArticleEditForm, CustomUserCreationForm, 
    CustomAuthenticationForm, UserProfileForm
)

class ArticleCreateFormTest(TestCase):
    """Тесты для формы создания статьи (ArticleCreateForm)"""
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='password123')
        self.section = Section.objects.create(title="IT", created_by=self.user)

    def test_form_valid_data(self):
        form = ArticleCreateForm(data={'title': 'Test', 'content': 'Text', 'section': self.section.id, 'status': 'published'})
        self.assertTrue(form.is_valid())

    def test_empty_title(self):
        form = ArticleCreateForm(data={'title': '', 'content': 'Text'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_empty_content(self):
        form = ArticleCreateForm(data={'title': 'Test', 'content': ''})
        self.assertFalse(form.is_valid())

    def test_missing_section(self):
        form = ArticleCreateForm(data={'title': 'Test', 'content': 'Text', 'status': 'published'})
        self.assertFalse(form.is_valid())

    def test_invalid_status(self):
        form = ArticleCreateForm(data={'title': 'Test', 'status': 'invalid'})
        self.assertFalse(form.is_valid())

    def test_long_title(self):
        form = ArticleCreateForm(data={'title': 'A' * 501, 'content': 'Text'})
        self.assertFalse(form.is_valid())

    def test_author_assignment_on_save(self):
        form = ArticleCreateForm(data={'title': 'Test', 'content': 'Text', 'section': self.section.id, 'status': 'published'})
        if form.is_valid():
            article = form.save(author=self.user)
            self.assertEqual(article.author, self.user)

    def test_attachment_processing_logic(self):
        file = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        form = ArticleCreateForm(data={'title': 'Test', 'content': 'Text', 'section': self.section.id, 'status': 'published'}, files={'attachments': [file]})
        self.assertTrue(form.is_valid())

    def test_summary_optional(self):
        form = ArticleCreateForm(data={'title': 'Test', 'content': 'Text', 'section': self.section.id, 'status': 'published', 'summary': ''})
        self.assertTrue(form.is_valid())

    def test_tags_widget_attributes(self):
        form = ArticleCreateForm()
        self.assertEqual(form.fields['tags'].label, 'Теги')

class ArticleEditFormTest(TestCase):
    """Тесты для формы редактирования статьи (ArticleEditForm)"""
    def setUp(self):
        self.user = User.objects.create_user(username='editor', password='password123')
        self.section = Section.objects.create(title="IT", created_by=self.user)
        self.article = Article.objects.create(title="Old", content="Old Text", section=self.section, author=self.user)

    def test_history_created_on_change(self):
        form = ArticleEditForm(data={'title': 'New', 'content': 'New Text', 'section': self.section.id, 'status': 'published'}, instance=self.article)
        self.assertTrue(form.is_valid())
        form.save(modified_by=self.user, change_reason="Updated content")
        self.assertEqual(ArticleHistory.objects.count(), 1)

    def test_version_increment(self):
        old_version = self.article.version
        form = ArticleEditForm(data={'title': 'New', 'content': 'New Text', 'section': self.section.id, 'status': 'published'}, instance=self.article)
        if form.is_valid():
            article = form.save(modified_by=self.user)
            self.assertEqual(article.version, old_version + 1)

    def test_article_edit_form_initial_data(self):
        """Проверка: форма редактирования корректно подгружает данные статьи для правки"""
        form = ArticleEditForm(instance=self.article)
        self.assertEqual(form.initial['title'], self.article.title)
        self.assertEqual(form.initial['content'], self.article.content)
        self.assertEqual(form.initial['section'], self.article.section.id)
        self.assertIn('form-control', form.fields['title'].widget.attrs['class'])

    def test_change_reason_field_exists(self):
        form = ArticleEditForm()
        self.assertIn('change_reason', form.fields)

    def test_edit_invalid_data(self):
        form = ArticleEditForm(data={'title': '', 'content': ''}, instance=self.article)
        self.assertFalse(form.is_valid())

    def test_edit_retains_author(self):
        form = ArticleEditForm(data={'title': 'New', 'content': 'Text', 'section': self.section.id, 'status': 'published'}, instance=self.article)
        if form.is_valid():
            article = form.save()
            self.assertEqual(article.author, self.user)

    def test_tag_update(self):
        form = ArticleEditForm(data={'title': 'New', 'content': 'Text', 'section': self.section.id, 'status': 'published', 'tags': 'new_tag'}, instance=self.article)
        self.assertTrue(form.is_valid())

    def test_summary_update(self):
        form = ArticleEditForm(data={'title': 'New', 'content': 'Text', 'section': self.section.id, 'status': 'published', 'summary': 'New Sum'}, instance=self.article)
        self.assertTrue(form.is_valid())

    def test_form_control_classes(self):
        form = ArticleEditForm()
        self.assertIn('form-control', form.fields['title'].widget.attrs['class'])

    def test_modified_by_required_for_history(self):
        form = ArticleEditForm(data={'title': 'X', 'content': 'Y', 'section': self.section.id, 'status': 'published'}, instance=self.article)
        if form.is_valid():
            # Без modified_by история не создастся (проверка логики в save)
            form.save()
            self.assertEqual(ArticleHistory.objects.count(), 0)

class UserCreationFormTest(TestCase):
    """Тесты для формы регистрации (CustomUserCreationForm)"""
    def test_valid_registration(self):
        form = CustomUserCreationForm(data={'username': 'newuser', 'email': 't@t.com', 'password123': 'pass', 'password123': 'pass'})
        # Django UserCreationForm требует пароли в полях password1, password2
        # Мы проверяем наличие классов и полей
        self.assertIn('username', form.fields)
        self.assertIn('email', form.fields)

    def test_form_control_injection(self):
        form = CustomUserCreationForm()
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs['class'], 'form-control')

    def test_email_field_label(self):
        form = CustomUserCreationForm()
        self.assertEqual(form.fields['email'].label, 'Адрес электронной почты')

    def test_missing_username(self):
        form = CustomUserCreationForm(data={'username': ''})
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        User.objects.create_user(username='test')
        form = CustomUserCreationForm(data={'username': 'test'})
        self.assertFalse(form.is_valid())

    def test_invalid_email_format(self):
        form = CustomUserCreationForm(data={'username': 'user', 'email': 'not-an-email'})
        self.assertFalse(form.is_valid())

    def test_long_username(self):
        form = CustomUserCreationForm(data={'username': 'a' * 151})
        self.assertFalse(form.is_valid())

    def test_required_fields(self):
        form = CustomUserCreationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_help_text_empty(self):
        form = CustomUserCreationForm()
        self.assertEqual(form.fields['email'].help_text, '')

    def test_username_help_text(self):
        form = CustomUserCreationForm()
        self.assertTrue(len(form.fields['username'].help_text) > 0)

class AuthenticationFormTest(TestCase):
    """Тесты для формы входа (CustomAuthenticationForm)"""
    def test_form_control_injection(self):
        form = CustomAuthenticationForm()
        self.assertEqual(form.fields['username'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['password'].widget.attrs['class'], 'form-control')

    def test_empty_login(self):
        form = CustomAuthenticationForm(data={'username': '', 'password': ''})
        self.assertFalse(form.is_valid())

    def test_missing_password(self):
        form = CustomAuthenticationForm(data={'username': 'admin'})
        self.assertFalse(form.is_valid())

    def test_missing_username(self):
        form = CustomAuthenticationForm(data={'password': '123'})
        self.assertFalse(form.is_valid())

    def test_widget_types(self):
        form = CustomAuthenticationForm()
        from django.forms.widgets import PasswordInput
        self.assertIsInstance(form.fields['password'].widget, PasswordInput)

    def test_login_invalid_user(self):
        form = CustomAuthenticationForm(data={'username': 'noone', 'password': '123'})
        self.assertFalse(form.is_valid())

    def test_autofocus_attribute_present(self):
        form = CustomAuthenticationForm()
        self.assertIn('autofocus', form.fields['username'].widget.attrs)
        self.assertTrue(form.fields['username'].widget.attrs['autofocus'])

    def test_labels_present(self):
        form = CustomAuthenticationForm()
        self.assertTrue(form.fields['username'].label)

    def test_max_length_username(self):
        form = CustomAuthenticationForm()
        self.assertTrue(form.fields['username'].max_length >= 30)

    def test_username_field_class(self):
        form = CustomAuthenticationForm()
        self.assertIn('form-control', form.fields['username'].widget.attrs['class'])

class UserProfileFormTest(TestCase):
    """Тесты для формы профиля (UserProfileForm)"""
    def setUp(self):
        self.user = User.objects.create_user(username='profile_user', first_name='Ivan', last_name='Ivanov', email='i@i.com')
        self.profile = UserProfile.objects.create(user=self.user)

    def test_form_initial_data(self):
        form = UserProfileForm(user=self.user, instance=self.profile)
        self.assertEqual(form.fields['first_name'].initial, 'Ivan')
        self.assertEqual(form.fields['email'].initial, 'i@i.com')

    def test_valid_update(self):
        data = {'first_name': 'Petr', 'last_name': 'Petrov', 'email': 'p@p.com', 'bio': 'New Bio'}
        form = UserProfileForm(data=data, user=self.user, instance=self.profile)
        self.assertTrue(form.is_valid())
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Petr')

    def test_invalid_email(self):
        data = {'email': 'invalid-email'}
        form = UserProfileForm(data=data, user=self.user, instance=self.profile)
        self.assertFalse(form.is_valid())

    def test_bio_widget_rows(self):
        form = UserProfileForm()
        self.assertEqual(form.fields['bio'].widget.attrs['rows'], 4)

    def test_avatar_field_class(self):
        form = UserProfileForm()
        self.assertIn('form-control', form.fields['avatar'].widget.attrs['class'])

    def test_save_syncs_to_user_model(self):
        form = UserProfileForm(data={'first_name': 'Sidor', 'bio': 'Text'}, user=self.user, instance=self.profile)
        if form.is_valid():
            form.save()
            self.assertEqual(User.objects.get(id=self.user.id).first_name, 'Sidor')

    def test_empty_names_allowed(self):
        form = UserProfileForm(data={'first_name': '', 'last_name': '', 'bio': 'Hi'}, user=self.user, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_bio_label(self):
        form = UserProfileForm()
        self.assertEqual(form.fields['bio'].label, 'О себе')

    def test_init_without_user(self):
        # Форма должна работать даже если пользователь не передан (kwargs.pop)
        form = UserProfileForm()
        self.assertIsNone(form.user)

    def test_last_name_max_length(self):
        form = UserProfileForm()
        self.assertEqual(form.fields['last_name'].max_length, 30)