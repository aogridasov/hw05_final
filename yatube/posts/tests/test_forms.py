import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='dummy')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.unauthorized_client = Client()

        Post.objects.create(
            pk=1,
            text='test_text_first_post',
            author=cls.user
        )

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_creation_form_updates_database(self):
        """Форма создания поста создаёт запись в базе данных"""
        post_count = Post.objects.count()

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

        form_data = {
            'text': 'test_text_new_post',
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'dummy'}
        )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(Post.objects.get(pk=2).text, form_data['text'])
        self.assertEqual(Post.objects.get(pk=2).image, 'posts/small.gif')
        self.assertIsNone(Post.objects.get(pk=2).group)

    def test_post_editing_form_updates_database(self):
        """Форма редактирвания поста изменяет запись в базе данных"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'test_text_changed',
            'group': self.group.id
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data,
            follow=True
        )

        updated_post = Post.objects.get(pk=1)

        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[1]
        )
        )
        self.assertEqual(updated_post.text, form_data['text'])
        self.assertEqual(updated_post.group.id, form_data['group'])

    def test_creation_form_not_update_database_for_unauthorized_user(self):
        """Неавторизированый пользователь не может создать пост"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'unauthorized text'
        }

        self.unauthorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(
            Post.objects.filter(text=form_data['text']).count(),
            0
        )

    def test_editing_form_not_update_database_for_unauthorized_user(self):
        """Неавторизированый пользователь не может редактировать пост"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'unauthorized text_change',
            'group': self.group.id
        }

        self.unauthorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group']
            ).count(),
            0
        )


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='dummy')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

        cls.post = Post.objects.create(
            text='',
            author=cls.user,
        )

    def test_comment_form_updates_database(self):
        """Форма написания комментария корректно
        создает запись в базе данных"""
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'test_text_new_comment',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(
            Comment.objects.get(post=self.post).text,
            form_data['text']
        )

    def test_creation_form_not_update_database_for_unauthorized_user(self):
        """Неавторизированый пользователь не может написать комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'unauthorized comment text'
        }

        self.unauthorized_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(
            Comment.objects.filter(text=form_data['text']).count(),
            0
        )
