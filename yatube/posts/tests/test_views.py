import shutil
import tempfile
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.views import Comment, Follow, Group, Post


User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Dima")
        cls.group = Group.objects.create(
            title="Тестовая группа паджинатора",
            slug="test-group-paginator",
            description="Группа для теста паджинатора",
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        for i in range(1, 16):
            post = Post.objects.create(
                text="Тестовый пост " + str(i),
                author=cls.user,
                group=cls.group,
            )
            post.pub_date = datetime(2015, 10, i, i, 55, 59, 342380)
            post.save()

        cls.posts = Post.objects.all()

    def setUp(self):
        cache.clear()

    def test_posts_pages_with_paginators(self):
        """
        Проверяем, соответствует ли ожиданиям
        словарь context cтраниц с паджинатором.
        """
        pages = {
            "posts:index": {},
            "posts:group_list": {"slug": self.group.slug},
            "posts:profile": {"username": self.user.username},
        }
        for page, args in pages.items():
            with self.subTest(page=page):
                response = self.auth_client.get(reverse(page, kwargs=args))
                self.assertEqual(len(response.context["page_obj"]), 10)
                response = self.auth_client.get(
                    reverse(page, kwargs=args) + "?page=2"
                )
                self.assertEqual(len(response.context["page_obj"]), 5)


class TestPostsView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Anton")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-group",
            description="Группа для теста",
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.post = Post.objects.create(
            text="Тестовый пост 123", author=cls.user, group=cls.group
        )

    def setUp(self):
        cache.clear()

    def test_posts_views_use_correct_tamplates(self):
        """Проверяем, что все view используют нужный шаблон."""
        tamplates_page_names = {
            "posts/index.html": reverse("posts:index"),
            "posts/group_list.html": reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ),
            "posts/profile.html": reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ),
            "posts/post_detail.html": reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ),
            "posts/create_post.html": reverse("posts:post_create"),
        }

        for template, reverse_name in tamplates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.auth_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        template = "posts/create_post.html"
        self.assertTemplateUsed(response, template)

    def test_posts_view_post_detail_context(self):
        """
        Проверяем, соответствует ли ожиданиям
        словарь context страницы /post_detail/.
        """
        response = self.auth_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        post_text = response.context["post"].text
        user_posts_count = response.context["posts_count"]
        user_id = response.context["user"]
        self.assertEqual(
            post_text, self.post.text, "В контекст не передаётся текст поста"
        )
        self.assertEqual(
            user_posts_count,
            self.post.author.posts.count(),
            "В контекст не передаётся количество постов автора",
        )
        self.assertEqual(
            user_id,
            self.post.author.id,
            "В контекст не передаётся айди автора",
        )

    def test_posts_view_post_edit_context(self):
        """
        Проверяем, соответствует ли ожиданиям
        словарь context страницы /post_edit/.
        """
        response = self.auth_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_object = response.context["form"]
        self.assertIsInstance(
            form_object,
            PostForm,
            "В контекст не передаётся форма редактирования поста",
        )

    def test_posts_view_post_create_context(self):
        """
        Проверяем, соответствует ли ожиданиям
        словарь context страницы /post_create/.
        """
        response = self.auth_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_object = response.context["form"]
        self.assertIsInstance(
            form_object,
            PostForm,
            "В контекст не передаётся форма создания поста",
        )

    def test_posts_view_post_create(self):
        """
        Проверяем, что если при создании поста
        указать группу, то этот пост появляется на главной странице сайта,
        на странице выбранной группы, в профайле пользователя."""
        pages = {
            "posts:index": {},
            "posts:group_list": {"slug": self.post.group.slug},
            "posts:profile": {"username": self.post.author.username},
        }

        for page, args in pages.items():
            with self.subTest(page=page):
                response = self.auth_client.get(reverse(page, kwargs=args))
                self.assertEqual(
                    response.context["page_obj"][self.post.id - 1], self.post
                )


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostsImage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="Tolya")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title="Тестовая группа для картинки",
            slug="test-group-image",
            description="Описание тестовой группы",
        )

        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый пост с картинкой",
            group=cls.group,
            author=cls.user,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_posts_image_in_context_first(self):
        """
        Проверяем, что при выводе поста с картинкой
        изображение передаётся в словаре context.
        """
        urls = [
            "/",
            f"/profile/{self.post.author}/",
            f"/group/{self.group.slug}/",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(
                    self.post.image,
                    response.context["page_obj"][self.post.id - 1].image,
                    f"Со страницей {url} произошла ошибка.",
                )

    def test_posts_image_in_context_second(self):
        """
        Проверяем, что при выводе поста с картинкой
        изображение передаётся в словаре context.
        """
        response = self.auth_client.get(f"/posts/{self.post.id}/")
        self.assertEqual(
            self.post.image,
            response.context[0]["post"].image,
            f"Со страницей /posts/{self.post.id}/ произошла ошибка.",
        )


class TestPostsCommnets(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Liza")
        cls.guest_client = Client()
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.post = Post.objects.create(text="Тестовый пост", author=cls.user)

    def test_posts_comments_login_required(self):
        """Проверяем, что комментировать могут только авторизованные юзеры."""
        form_data = {"text": "hello, friend"}
        response = self.guest_client.post(
            f"/posts/{self.post.id}/comment/", data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            f"/auth/login/?next=/posts/{self.post.id}/comment/",
            msg_prefix="Редирект работает не правильно",
        )
        count = Comment.objects.filter(post=self.post).count()
        self.auth_client.post(
            f"/posts/{self.post.id}/comment/", data=form_data, follow=True
        )
        new_count = Comment.objects.filter(post=self.post).count()
        self.assertEqual(
            new_count,
            count + 1,
            "Комментарии не создаются авторизованным пользователем.",
        )

    def test_posts_comments_appear_on_the_page(self):
        """
        Проверяем, после успешной отправки
        комментарий появляется на странице поста.
        """
        form_data = {"text": "test_comment"}
        self.auth_client.post(
            f"/posts/{self.post.id}/comment/", data=form_data, follow=True
        )
        response = self.guest_client.get(f"/posts/{self.post.id}/")
        self.assertEqual(
            form_data["text"],
            response.context["comments"][0].text,
            "Комментарии не появляются на странице",
        )


class TestPostsIndexCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Ira")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.post = Post.objects.create(text="Тест кеша", author=cls.user)

    def test_posts_cache_working(self):
        """Проверяем работу кеша на главной странице."""
        response_one = self.auth_client.get(reverse("posts:index"))
        self.post.delete()
        response_two = self.auth_client.get(reverse("posts:index"))
        self.assertEqual(
            response_one.content,
            response_two.content,
            "Главная страница не кешируется",
        )
        cache.clear()
        response_three = self.auth_client.get(reverse("posts:index"))
        self.assertNotEqual(
            response_two.content,
            response_three.content,
            "Кеш отчищен, но контент не изменился.",
        )


class TestPostsFollows(TestCase):
    def setUp(self):

        self.first_user = User.objects.create_user(username="first")
        self.second_user = User.objects.create_user(username="second")
        self.third_user = User.objects.create_user(username="third")

        self.first_auth_client = Client()
        self.second_auth_client = Client()
        self.third_auth_client = Client()

        self.first_auth_client.force_login(self.first_user)
        self.second_auth_client.force_login(self.second_user)
        self.third_auth_client.force_login(self.third_user)

        Follow.objects.create(author=self.second_user, user=self.first_user)

    def test_posts_follows_working(self):
        """
        Проверяем, что авторизованный пользователь
        может подписываться на других пользователей
        и удалять их из подписок.
        """
        self.second_auth_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.third_user.username},
            )
        )
        follow = Follow.objects.get(user=self.second_user)
        self.assertEqual(
            follow.user == self.second_user,
            follow.author == self.third_user,
            "Подписки не работают.",
        )

        self.first_auth_client.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.second_user.username},
            )
        )
        try:
            follow = Follow.objects.get(user=self.first_user)
            follow = False
        except Follow.DoesNotExist:
            follow = True
        self.assertTrue(follow, "Отписки не работают.")

    def test_posts_followed_users_see_only_needed_posts(self):
        """Проверяем, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        self.second_auth_client.post(
            reverse("posts:post_create"),
            data={"text": "hello, my subcribers 1"},
        )
        self.second_auth_client.post(
            reverse("posts:post_create"),
            data={"text": "hello, my subcribers 2"},
        )
        self.second_auth_client.post(
            reverse("posts:post_create"),
            data={"text": "hello, my subcribers 3"},
        )
        response_by_follower = self.first_auth_client.get(
            reverse("posts:follow_index")
        )
        response_by_not_follower = self.third_auth_client.get(
            reverse("posts:follow_index")
        )
        self.assertNotEqual(
            response_by_not_follower,
            response_by_follower,
            "С появлением избранных постов что-то не так.",
        )
