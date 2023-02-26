from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='GeorgiyGyrdzhiev')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTests.user)

    def test_cache_index(self):
        """Проверка кэширования поста в шаблоне index"""
        first_upd = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененный тестовый пост'
        post.save()
        second_upd = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            first_upd.content,
            second_upd.content,
            'Содержимое шаблона различается'
        )
        cache.clear()
        third_upd = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(
            first_upd.content,
            third_upd.content,
            'Содержимое шаблона совпадает'
        )
