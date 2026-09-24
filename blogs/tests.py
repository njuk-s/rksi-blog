"""Тесты блога.

Обязательные проверки из задания отмечены в docstring: порядок публикаций,
пустое состояние, чтение без входа, запрет создания без входа, назначение
автора, редактирование автором, запрет редактирования чужой публикации,
404 для отсутствующего ID, регистрация, выход только через POST
(последние две - в users/tests.py).
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import BlogPost, Comment


class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anna = User.objects.create_user('anna', password='pass-12345')
        cls.boris = User.objects.create_user('boris', password='pass-12345')
        cls.post = BlogPost.objects.create(owner=cls.anna, title='Пост Анны', text='Текст Анны')


class HomeTests(BaseCase):
    def test_newest_posts_first(self):
        """Обязательный: порядок публикаций на главной."""
        older = BlogPost.objects.create(owner=self.boris, title='Старый', text='...')
        newer = BlogPost.objects.create(owner=self.boris, title='Новый', text='...')
        BlogPost.objects.filter(id=older.id).update(date_added=timezone.now() - timedelta(days=2))
        BlogPost.objects.filter(id=self.post.id).update(date_added=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse('blogs:index'))
        self.assertEqual([p.title for p in response.context['posts']], ['Новый', 'Пост Анны', 'Старый'])
        self.assertLess(response.content.decode().index('Новый'), response.content.decode().index('Старый'))
        self.assertTrue(newer)

    def test_empty_state(self):
        """Обязательный: отображение пустого состояния."""
        BlogPost.objects.all().delete()
        response = self.client.get(reverse('blogs:index'))
        self.assertContains(response, 'Публикаций пока нет')

    def test_anonymous_can_read(self):
        """Обязательный: доступность чтения без входа."""
        response = self.client.get(reverse('blogs:index'))
        self.assertContains(response, 'Пост Анны')
        self.assertContains(response, 'anna')
        self.assertNotContains(response, reverse('blogs:new'))
        detail = self.client.get(reverse('blogs:detail', args=[self.post.id]))
        self.assertContains(detail, 'Текст Анны')

    def test_edit_link_only_for_author(self):
        edit_url = reverse('blogs:edit', args=[self.post.id])
        self.client.force_login(self.boris)
        self.assertNotContains(self.client.get(reverse('blogs:index')), edit_url)
        self.client.force_login(self.anna)
        self.assertContains(self.client.get(reverse('blogs:index')), edit_url)

    def test_search(self):
        BlogPost.objects.create(owner=self.boris, title='Про Docker', text='контейнеры')
        response = self.client.get(reverse('blogs:index'), {'q': 'КОНТЕЙНЕРЫ'})
        self.assertEqual([p.title for p in response.context['posts']], ['Про Docker'])

    def test_pagination(self):
        for i in range(7):
            BlogPost.objects.create(owner=self.boris, title=f'Пост {i}', text='...')
        response = self.client.get(reverse('blogs:index'), {'page': 2})
        self.assertEqual(len(response.context['posts']), 3)


class CreateTests(BaseCase):
    def test_anonymous_cannot_create(self):
        """Обязательный: запрет создания без входа."""
        url = reverse('blogs:new')
        self.assertRedirects(self.client.get(url), f"{reverse('users:login')}?next={url}")
        self.client.post(url, {'title': 'X', 'text': 'Y'})
        self.assertFalse(BlogPost.objects.filter(title='X').exists())

    def test_author_is_assigned(self):
        """Обязательный: автоматическое назначение автора, подмена owner игнорируется."""
        self.client.force_login(self.boris)
        self.client.post(reverse('blogs:new'), {
            'title': 'Новый пост', 'text': 'Текст', 'owner': self.anna.id, 'action': 'publish',
        })
        post = BlogPost.objects.get(title='Новый пост')
        self.assertEqual(post.owner, self.boris)
        self.assertTrue(post.is_published)

    def test_empty_form_shows_errors(self):
        self.client.force_login(self.boris)
        response = self.client.post(reverse('blogs:new'), {'title': '', 'text': ''})
        self.assertEqual(set(response.context['form'].errors), {'title', 'text'})


class EditTests(BaseCase):
    def test_author_can_edit(self):
        """Обязательный: возможность автора редактировать публикацию."""
        self.client.force_login(self.anna)
        self.client.post(reverse('blogs:edit', args=[self.post.id]),
                         {'title': 'Исправлено', 'text': 'Новый текст', 'action': 'save'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Исправлено')
        self.assertEqual(self.post.owner, self.anna)

    def test_cannot_edit_foreign_post(self):
        """Обязательный: запрет редактирования чужой публикации (404)."""
        self.client.force_login(self.boris)
        url = reverse('blogs:edit', args=[self.post.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'title': 'взлом', 'text': 'взлом'}).status_code, 404)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Пост Анны')

    def test_owner_cannot_be_changed_by_post(self):
        self.client.force_login(self.anna)
        self.client.post(reverse('blogs:edit', args=[self.post.id]),
                         {'title': 'T', 'text': 'T', 'owner': self.boris.id})
        self.post.refresh_from_db()
        self.assertEqual(self.post.owner, self.anna)

    def test_missing_id_is_404(self):
        """Обязательный: ответ 404 для отсутствующего ID."""
        self.client.force_login(self.anna)
        for name in ('detail', 'edit', 'delete'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f'blogs:{name}', args=[99999])).status_code, 404)

    def test_anonymous_edit_redirects_to_login(self):
        url = reverse('blogs:edit', args=[self.post.id])
        self.assertRedirects(self.client.get(url), f"{reverse('users:login')}?next={url}")


class DeleteTests(BaseCase):
    def test_get_asks_confirmation(self):
        self.client.force_login(self.anna)
        response = self.client.get(reverse('blogs:delete', args=[self.post.id]))
        self.assertContains(response, 'Да, удалить')
        self.assertTrue(BlogPost.objects.filter(id=self.post.id).exists())

    def test_author_deletes_by_post(self):
        self.client.force_login(self.anna)
        self.client.post(reverse('blogs:delete', args=[self.post.id]))
        self.assertFalse(BlogPost.objects.filter(id=self.post.id).exists())

    def test_foreign_delete_is_404(self):
        self.client.force_login(self.boris)
        self.assertEqual(self.client.post(reverse('blogs:delete', args=[self.post.id])).status_code, 404)
        self.assertTrue(BlogPost.objects.filter(id=self.post.id).exists())


class DraftTests(BaseCase):
    def setUp(self):
        self.draft = BlogPost.objects.create(owner=self.anna, title='Секретный черновик', text='...',
                                             is_published=False)

    def test_draft_hidden_from_others(self):
        self.assertNotContains(self.client.get(reverse('blogs:index')), 'Секретный черновик')
        self.assertEqual(self.client.get(reverse('blogs:detail', args=[self.draft.id])).status_code, 404)
        self.client.force_login(self.boris)
        self.assertEqual(self.client.get(reverse('blogs:detail', args=[self.draft.id])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('blogs:author', args=['anna'])), 'Секретный черновик')

    def test_author_sees_and_publishes_draft(self):
        self.client.force_login(self.anna)
        self.assertContains(self.client.get(reverse('blogs:author', args=['anna'])), 'Секретный черновик')
        self.client.post(reverse('blogs:edit', args=[self.draft.id]),
                         {'title': 'Секретный черновик', 'text': '...', 'action': 'publish'})
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.is_published)

    def test_save_as_draft(self):
        self.client.force_login(self.boris)
        self.client.post(reverse('blogs:new'), {'title': 'Набросок', 'text': '...', 'action': 'draft'})
        self.assertFalse(BlogPost.objects.get(title='Набросок').is_published)


class CommentTests(BaseCase):
    def test_anonymous_cannot_comment(self):
        self.client.post(reverse('blogs:comment_add', args=[self.post.id]), {'text': 'спам'})
        self.assertFalse(Comment.objects.exists())

    def test_user_comments_and_author_is_assigned(self):
        self.client.force_login(self.boris)
        self.client.post(reverse('blogs:comment_add', args=[self.post.id]),
                         {'text': 'Отличный пост', 'author': self.anna.id})
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.boris)
        self.assertContains(self.client.get(reverse('blogs:detail', args=[self.post.id])), 'Отличный пост')

    def test_comment_delete_rights(self):
        carl = User.objects.create_user('carl')
        comment = Comment.objects.create(post=self.post, author=self.boris, text='Коммент')
        url = reverse('blogs:comment_delete', args=[comment.id])
        self.client.force_login(carl)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.boris)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_login(self.anna)  # автор публикации может удалить чужой комментарий
        self.client.post(url)
        self.assertFalse(Comment.objects.exists())

    def test_empty_comment_rejected(self):
        self.client.force_login(self.boris)
        self.client.post(reverse('blogs:comment_add', args=[self.post.id]), {'text': '   '})
        self.assertFalse(Comment.objects.exists())


class ModelTests(BaseCase):
    def test_str_returns_title(self):
        self.assertEqual(str(self.post), 'Пост Анны')


class OwnerMigrationTests(TransactionTestCase):
    """Публикации, созданные до появления автора, получают существующего пользователя."""

    before = [('blogs', '0001_initial')]
    after = [('blogs', '0002_blogpost_owner')]
    auth = [('auth', '0012_alter_user_first_name_max_length')]

    def test_existing_posts_get_owner(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old_apps = executor.loader.project_state(self.before + self.auth).apps
        admin = old_apps.get_model('auth', 'User').objects.create(username='admin', is_superuser=True)
        for i in range(3):
            old_apps.get_model('blogs', 'BlogPost').objects.create(title=f'Старый {i}', text='...')

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.after)
        new_apps = executor.loader.project_state(self.after).apps
        owners = set(new_apps.get_model('blogs', 'BlogPost').objects.values_list('owner_id', flat=True))
        self.assertEqual(owners, {admin.id})

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
