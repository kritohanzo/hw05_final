from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post


User = get_user_model()


class TestPostsModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост тестовый пост тестовый пост"
        )

    def test_posts_models_have_correct_method_str(self):
        """
        Проверяем, что у моделей
        корректно работает __str__.
        """
        models = {self.post: self.post.text[:15], self.group: self.group.title}
        for model, expected in models.items():
            with self.subTest(model=model, expected=expected):
                self.assertEqual(str(model), expected)

    def test_posts_models_have_correct_verbose_name(self):
        """
        Проверяем, что у моделей
        корректно работает verbose_name.
        """
        post = self.post
        field_verbose_names = {
            "text": "Текст поста",
            "pub_date": "Дата создания",
            "author": "Автор",
            "group": "Группа",
        }
        for field, expected_value in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_models_have_correct_help_text(self):
        """
        Проверяем, что у моделей
        корректно работает help_text.
        """
        post = self.post
        field_help_texts = {
            "text": "Текст поста, который увидят пользователи",
            "group": "Группа, к которой будет относиться запись",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
