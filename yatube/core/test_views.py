from django.test import Client, TestCase


class TestCoreViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_core_404_use_correct_templates(self):
        """Проверяем, что кастомная 404 ошибка использует нужный шаблон."""
        response = self.guest_client.get("/abcdefg/")
        self.assertTemplateUsed(response, "core/404.html")
