"""
Наполняет пустой блог демонстрационными публикациями для проверки.

Создаёт авторов anna и boris с паролем из DEMO_PASSWORD, несколько
публикаций, черновик и комментарии. Повторный запуск ничего не дублирует.
Без DEMO_PASSWORD команда ничего не делает.
"""
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from blogs.models import BlogPost

POSTS = [
    ('anna', 'Почему я веду учебный журнал',
     'Раньше я читала документацию и через неделю всё забывала.\n\n'
     'Теперь после каждого занятия записываю три вещи: что узнала, что не получилось '
     'и что попробую завтра. Через месяц видно, как далеко продвинулась.', True),
    ('boris', 'Docker Compose за один вечер',
     'Главное, что нужно понять: контейнер - это не виртуальная машина. '
     'Данные, которые должны пережить пересоздание контейнера, храните на томе.\n\n'
     'Для Django это база SQLite. Миграции удобно запускать прямо в команде запуска контейнера.', True),
    ('anna', 'Проверка владельца в Django',
     'Скрыть кнопку «Редактировать» в шаблоне недостаточно: URL можно набрать вручную.\n\n'
     'Надёжный способ - получать объект сразу с условием по автору:\n'
     'get_object_or_404(BlogPost, id=post_id, owner=request.user).\n\n'
     'Тогда чужая запись просто не находится, и пользователь получает 404.', True),
    ('boris', 'Черновик: планы на следующий семестр',
     'Этот текст видит только boris - это черновик.', False),
]

COMMENTS = [
    ('Проверка владельца в Django', 'boris', 'Попробовал открыть /posts/<id>/edit/ для твоей записи - действительно 404.'),
    ('Docker Compose за один вечер', 'anna', 'Спасибо, про том для SQLite очень полезно!'),
]


class Command(BaseCommand):
    help = 'Создать демо-авторов anna и boris с публикациями и комментариями.'

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD', '')
        if not password:
            self.stdout.write('seed_demo: DEMO_PASSWORD не задан, пропускаю.')
            return

        users = {}
        for username in ('anna', 'boris'):
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            users[username] = user

        if BlogPost.objects.filter(owner__in=users.values()).exists():
            return

        # Публикации создаются по очереди, поэтому последняя окажется на главной первой.
        posts = {}
        for username, title, text, published in POSTS:
            posts[title] = BlogPost.objects.create(owner=users[username], title=title, text=text,
                                                   is_published=published)
        for title, username, text in COMMENTS:
            posts[title].comments.create(author=users[username], text=text)
        self.stdout.write('seed_demo: демо-публикации созданы.')
