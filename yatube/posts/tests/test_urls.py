from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user_author = User.objects.create_user(username="post_author")
        cls.user_not_author = User.objects.create_user(
            username="post_not_author"
        )

        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.user_author)

        cls.auth_client_not_author = Client()
        cls.auth_client_not_author.force_login(cls.user_not_author)

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-group",
            description="Тестовое описание группы",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.user_author, group=cls.group
        )

    def test_posts_public_urls(self):
        """
        Проверяем, что публичные страницы
        работают с анонимным пользователем.
        """
        public_urls = {
            "/": HTTPStatus.OK,
            "/group/test-group/": HTTPStatus.OK,
            "/profile/post_author/": HTTPStatus.OK,
            f"/posts/{self.post.id}/": HTTPStatus.OK,
            "/unexisting_page/": HTTPStatus.NOT_FOUND,
        }
        for url, status_code in public_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEquals(
                    response.status_code,
                    status_code,
                    f"Страница {url} работает не правильно",
                )

    def test_posts_url_login_required(self):
        """
        Проверяем, что у страниц /create/ и /posts/post_id/edit/
        работают редиректы на логин с анонимным пользователем.
        """
        public_urls = {
            "/create/": "/auth/login/?next=/create/",
            f"/posts/{self.post.id}/edit/": "/auth/login/?next="
            f"/posts/{self.post.id}/edit/",
        }
        for url, redirect_url_with_follow in public_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    redirect_url_with_follow,
                    msg_prefix=f"Страница {url} работает не правильно",
                )

    def test_posts_edit_by_author(self):
        """
        Проверяем, что cтраница /posts/post_id/edit/
        работает с автором.
        """
        response = self.auth_client_author.get(f"/posts/{self.post.id}/edit/")
        self.assertEquals(
            response.status_code,
            HTTPStatus.OK,
            f"Страница /posts/{self.post.id}/edit/ работает "
            "не правильно с пользователем-автором.",
        )

    def test_posts_edit_by_not_author(self):
        """
        Проверяем, что cтраница /posts/post_id/edit/
        не даёт редактировать пост если клиент - не автор.
        """
        response = self.auth_client_not_author.get(
            f"/posts/{self.post.id}/edit/"
        )
        self.assertRedirects(
            response,
            f"/posts/{self.post.id}/",
            msg_prefix=f"Страница /posts/{self.post.id}/edit/ работает "
            "не правильно, если пользователь не автор.",
        )

    def test_posts_pages_use_correct_templates(self):
        """
        Проверяем, что все страницы
        используют правильные шаблоны.
        """
        url_templates = {
            "/": "posts/index.html",
            "/group/test-group/": "posts/group_list.html",
            "/profile/post_author/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.auth_client_author.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f"Страница {url} показывает неправильный шаблон",
                )
