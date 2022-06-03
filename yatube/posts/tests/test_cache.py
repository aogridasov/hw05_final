from django.core.cache import cache

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class PostsCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='dummy')
        cls.guest_client = Client()

    def test_cache_works_with_posts_at_index_page(self):
        """Кеширование списка постов корректно происходит
        на главной странице"""

        cached_post = Post.objects.create(
            pk=1,
            author=self.user,
            text='test_text'
        )

        response_1 = self.guest_client.get(reverse('posts:index'))

        cached_post.delete()
        response_2 = self.guest_client.get(reverse('posts:index'))

        self.assertEqual(response_1.content, response_2.content)

        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))

        self.assertNotEqual(response_2.content, response_3.content)
