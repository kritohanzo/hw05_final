from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm


User = get_user_model()


class UsersTestViewsTemplates(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.auth_client = Client()
        cls.user = User.objects.create_user(username="Dimka")
        cls.auth_client.force_login(cls.user)

    def test_users_reverse_public_urls_use_correct_template(self):
        """
        Проверяем, что реверсивные urls
        работают с нужными шаблонами на страницах, где не нужен логин.
        """
        reverse_urls = {
            "users:signup": "users/signup.html",
            "users:login": "users/login.html",
            "users:password_reset_form": "users/password_reset_form.html",
            "users:password_reset_done": "users/password_reset_done.html",
            "users:password_reset_complete": "users"
            "/password_reset_complete.html",
        }
        for reverse_url, template in reverse_urls.items():
            with self.subTest(reverse_url=reverse_url):
                response = self.guest_client.get(reverse(reverse_url))
                self.assertTemplateUsed(
                    response,
                    template,
                    f"Reverse url {reverse_url} работает не с тем шаблоном",
                )

    def test_users_reverse_login_required_urls_use_correct_template(self):
        """
        Проверяем, что реверсивные urls
        работают с нужными шаблонами на страницах, где нужен логин.
        """
        reverse_urls = {
            "users:password_change_form": "users/password_change_form.html",
            "users:password_change_done": "users/password_change_done.html",
            "users:logout": "users/logged_out.html",
        }
        for reverse_url, template in reverse_urls.items():
            with self.subTest(reverse_url=reverse_url):
                response = self.auth_client.get(reverse(reverse_url))
                self.assertTemplateUsed(
                    response,
                    template,
                    f"Reverse url {reverse_url} работает не с тем шаблоном",
                )

    def test_users_signup_form_context(self):
        """
        Проверяем, что страница signup передаёт форму
        для создания нового пользователя в контекст.
        """
        response = self.guest_client.get(reverse("users:signup"))
        self.assertIsInstance(
            response.context["form"],
            CreationForm,
            "В контекст users:signup передаётся не та форма.",
        )
