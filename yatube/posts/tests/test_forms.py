import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Проверяем, что валдидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text=form_data.get('text')).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Проверяем, что валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Изменение текста', 'group': self.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(text=form_data.get('text')).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_image_in_group_list_page(self):
        """Проверяем, что картинка передается на страницу group_list."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        obj = response.context['page_obj'][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Проверяем, что картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        obj = response.context['post']
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Проверяем, что картинка передается на страницы index и profile."""
        templates = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context['page_obj'][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем, что пост с картинкой создается в БД."""
        response = self.authorized_client.post(
            reverse('posts:post_create'), follow=True
        )
        self.assertTrue(
            response,
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )
