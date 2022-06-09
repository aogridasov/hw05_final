from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='auth')

        Post.objects.create(
            pk=1,
            author=cls.user,
            text='test text' * 100
        )

        Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.user2 = User.objects.create(username='another')
        cls.another_authorized_client = Client()
        cls.another_authorized_client.force_login(cls.user2)

    def test_urls_exist_at_desired_location_for_guest_user(self):
        """Страницы, доступные любому пользователю работают
           + несуществующая страница -> 404."""
        urls_http_status_code = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/auth/': 200,
            '/posts/1/': 200,
            '/i_dont_belong_here_page/': 404,
        }

        for adress, status_code in urls_http_status_code.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_create_url_redirects_anonymous_on_auth_login(self):
        """Страница создания поста перенаправляет
           неавторизованного пользователя на авторизацию"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_create_url_works_for_authorized_user(self):
        """Страница создания поста открывается для
           авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_works_for_author(self):
        """Страница редактирования поста открывается для
           автора поста"""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_redirects_non_author_on_post_page(self):
        """Страница редактирования поста перенаправляет
           не автора на страницу просмотра поста """
        response = self.another_authorized_client.get(
            '/posts/1/edit/',
            follow=True
        )
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        adress_templates = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/invalid_adress/': 'core/404.html',
        }

        for adress, template in adress_templates.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
