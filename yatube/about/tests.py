from http import HTTPStatus

from django.test import Client, TestCase


class TestURLAbout(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_about_urls(self):
        """Проверяем, что все ссылки работают исправно."""
        urls = {"/about/author/": HTTPStatus.OK, "/about/tech/": HTTPStatus.OK}
        for url, status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    status,
                    f"Ссылка {url} работает не правильно.",
                )

    def test_about_urls_use_correct_template(self):
        """Проверяем, что все ссылки используют нужные шаблоны."""
        urls = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f"Ссылка {url} работает c неправильным шаблоном.",
                )
