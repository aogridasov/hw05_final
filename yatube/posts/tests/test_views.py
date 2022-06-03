import shutil
import tempfile
import time

from django import forms

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        Post.objects.create(
            pk=1,
            author=cls.user,
            text='test_text' * 100,
        )

        time.sleep(0.001)

        Post.objects.create(
            pk=2,
            author=cls.user,
            text='test_text_2' * 100,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group',
                args=['test-slug']
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=['auth']
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=['1']
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                args=['1']
            ): 'posts/create_post.html',
        }

        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_list_show_correct_contsxt(self):
        """Шаблоны со списком постов формируются с правильным контекстом"""
        reverse_pages_list = [
            reverse('posts:index'),
            reverse('posts:group', args=['test-slug']),
            reverse('posts:profile', args=['auth']),
        ]

        for reverse_name in reverse_pages_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                test_post = response.context['page_obj'].object_list[0]
                self.assertEqual(test_post.pk, 2)
                self.assertEqual(test_post.author, self.user)
                self.assertEqual(test_post.text, 'test_text_2' * 100)
                self.assertEqual(test_post.image, 'posts/small.gif')

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=['2'])
        )
        test_post = response.context['post']
        self.assertEqual(test_post.pk, 2)
        self.assertEqual(test_post.author, self.user)
        self.assertEqual(test_post.text, 'test_text_2' * 100)
        self.assertEqual(test_post.image, 'posts/small.gif')

    def test_post_create_page_shows_correct_context_while_creating(self):
        """Шаблон post_create сформирован с правильным контекстом
        при создании поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_shows_correct_context_while_creating(self):
        """Шаблон post_create сформирован с правильным контекстом
        при редактировании поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=['1'])
        )
        post = response.context.get('form').instance
        self.assertEqual(post.pk, 1)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='dummy')

        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )

        for i in range(1, 12):
            Post.objects.create(
                pk=i,
                author=cls.user,
                text='test_text' * 100,
                group=cls.group
            )
            time.sleep(0.001)

    def test_first_page_contains_ten_records(self):
        """Паджинатор на первой странице в шаблонах index/group_list/profile
        обрезает корректное количество постов."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group', args=['test-slug']),
            reverse('posts:profile', args=['dummy']),
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                posts_count = len(response.context['page_obj'])
                self.assertEqual(posts_count, 10)

    def test_second_page_contains_ten_records(self):
        """Паджинатор на второй странице в шаблонах index/group_list/profile
        выдаёт корректное количество постов."""
        pages = [
            (reverse('posts:index')) + '?page=2',
            (reverse('posts:group', args=['test-slug'])) + '?page=2',
            (reverse(
                'posts:profile', args=['dummy']
            )) + '?page=2'
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                posts_count = len(response.context['page_obj'])
                self.assertEqual(posts_count, 1)


class PostGroupTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='dummy')

        cls.group_1 = Group.objects.create(
            title='test group 1',
            slug='test-slug-group-1',
            description='test description'
        )

        cls.group_2 = Group.objects.create(
            title='test group 2',
            slug='test-slug-group-2',
            description='test description'
        )

        Post.objects.create(
            pk=1,
            author=cls.user,
            text='test_text 1',
            group=cls.group_1
        )
        time.sleep(0.001)
        cls.post_2 = Post.objects.create(
            pk=2,
            author=cls.user,
            text='test_text 2',
            group=cls.group_2
        )

    def test_post_appears_at_corret_pages(self):
        """Пост появляется на станицах index, своей группы
        group_list и profile."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group', args=['test-slug-group-2']),
            reverse('posts:profile', args=['dummy'])
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                post = response.context['page_obj'][0]
                self.assertEqual(post, self.post_2)

    def test_post_does_not_appear_at_incorrect_group_gape(self):
        """Пост НЕ появляется на станице сторонней группы."""
        response = self.client.get(
            reverse('posts:group', args=['test-slug-group-1'])
        )
        post = response.context['page_obj'][0]
        self.assertNotEqual(post, self.post_2)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(username='author')
        cls.follower = User.objects.create(username='follower')
        cls.not_follower = User.objects.create(username='not_follower')

        cls.follower_client = Client()
        cls.not_follower_client = Client()

        cls.follower_client.force_login(cls.follower)
        cls.not_follower_client.force_login(cls.not_follower)

    def test_authorized_user_can_follow_and_unfollow_authors(self):
        """Авторизированный пользователь может подписываться на авторов и
        отписываться от них"""
        self.follower_client.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

        self.follower_client.get(
            reverse('posts:profile_unfollow', args=[self.author.username])
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

    def test_new_post_correctly_appears_in_feed(self):
        """Новый пост отображается в ленте подписанных пользователей
        и не отображается у остальных."""

        test_post = Post.objects.create(author=self.author, text='test_text')
        self.follower_client.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )

        follower_response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        not_follower_response = self.not_follower_client.get(
            reverse('posts:follow_index')
        )

        self.assertContains(follower_response, test_post)
        self.assertNotContains(not_follower_response, test_post)
