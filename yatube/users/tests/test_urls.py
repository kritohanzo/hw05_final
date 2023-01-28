from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


User = get_user_model()


class TestURLUsers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username="auth")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_users_public_urls(self):
        """
        Проверяем, что все публичные страницы
        корректно работают с анонимным клиентом.
        """
        urls = {
            "/auth/logout/": HTTPStatus.OK,
            "/auth/signup/": HTTPStatus.OK,
            "/auth/login/": HTTPStatus.OK,
            "/auth/password_reset/": HTTPStatus.OK,
            "/auth/password_reset/done/": HTTPStatus.OK,
            "/auth/reset/done/": HTTPStatus.OK,
        }

        for url, status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    status,
                    f"Страница {url} работает не правильно",
                )

    def test_users_url_login_required(self):
        """
        Проверяем, что определённые страницы
        редиректят анонимный клиент на логин.
        """
        urls = {
            "/auth/password_change/": "/auth/login/"
            "?next=/auth/password_change/",
            "/auth/password_change/done/": "/auth/login/"
            "?next=/auth/password_change/done/",
        }

        for url, expected_url in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    expected_url,
                    msg_prefix=f"Страница {url} работает не правильно",
                )

    def test_users_pages_use_correct_templates(self):
        """
        Проверяем, что все страницы
        работают с нужным шаблоном.
        """
        urls = {
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
            "/auth/password_reset/": "users/password_reset_form.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
            "/auth/reset/done/": "users/password_reset_complete.html",
            "/auth/logout/": "users/logged_out.html",
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
        }

        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(
                    response, template, f"Страница {url} работает не правильно"
                )
