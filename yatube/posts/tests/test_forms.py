from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()


class TestPostsForms(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Dimon")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-group",
            description="Описание тестовой группы",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост 123", author=cls.user
        )

    def test_posts_valid_form_creates_post(self):
        """
        Проверяем, что в случае отправки валидной формы
        создаётся новый пост в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {"text": "Тестовый пост"}
        self.auth_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(
            Post.objects.count(), posts_count + 1, "Посты не создаются"
        )
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый пост", author=self.user.id
            ).exists(),
            "Посты не создаются",
        )

    def test_posts_valid_form_edits_post(self):
        """
        Проверяем, что в случае отправки валидной формы
        редактируется пост в базе данных.
        """
        form_data = {"text": "Уже не тестовый пост =)", "group": self.group.id}
        self.auth_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        edited_post = Post.objects.get(id=self.post.id)
        self.assertEqual(
            edited_post.text, form_data["text"], "Текст поста не изменился"
        )
        self.assertEqual(
            edited_post.group.id,
            form_data["group"],
            "Группа поста не изменилась",
        )

    def test_posts_valid_form_with_image_create_post(self):
        """
        Проверяем, что при отправке поста с картинкой
        через форму PostForm создаётся запись в базе данных.
        """
        count = Post.objects.count()

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        Post.objects.create(
            text="Тестовый пост 2",
            author=self.user,
            group=self.group,
            image=uploaded,
        )
        new_count = Post.objects.count()
        self.assertEqual(
            new_count, count + 1, "Посты с картинками не создаются."
        )
