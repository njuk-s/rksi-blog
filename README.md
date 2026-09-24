# Блог

[![tests](https://github.com/njuk-s/rksi-blog/actions/workflows/ci.yml/badge.svg)](https://github.com/njuk-s/rksi-blog/actions/workflows/ci.yml)

Открытый блог: читают все, пишут зарегистрированные авторы, изменяет только автор.

**Работающий сайт:** https://njuk-blog.onrender.com

Учебный проект на Django 5.2 LTS (РКСИ, курс «Python & Django»).

## Как проверить

На сайте уже есть демонстрационные данные и два пользователя, чтобы сразу проверить разграничение доступа:

| Логин | Пароль |
|---|---|
| `anna` | передан вместе со ссылкой на работу |
| `boris` | тот же |
| `review_admin` (админка `/admin/`) | передан вместе со ссылкой на работу |

Можно и зарегистрировать собственных пользователей. Войдите под `anna`, запомните адрес любого её объекта,
затем войдите под `boris` и откройте этот адрес вручную - ответ будет 404.

## Возможности

Обязательная часть:

- Модель `BlogPost` (`title`, `text`, `date_added`, `owner`), `__str__()` возвращает заголовок.
- Главная со всеми публикациями, новые первыми; понятное сообщение, если записей нет.
- Для каждой записи: заголовок, автор, дата и время, фрагмент текста, ссылка редактирования только для автора.
- `BlogPostForm` (только `title` и `text`) для создания и редактирования; автор назначается в представлении.
- Регистрация с автоматическим входом, вход, выход **только POST-формой** с CSRF.
- Изменять запись может только автор: `get_object_or_404(BlogPost, id=post_id, owner=request.user)`.
- Автор добавлен отдельной миграцией: существующие записи получают существующего пользователя, без `default=1` в модели.
- Админка: список, заголовок, автор, дата, поиск по заголовку и тексту, фильтры по дате, автору и статусу.
- Bootstrap 4 через `django-bootstrap4`, карточки, адаптивно для телефона; длинный текст не ломает ширину.

Дополнительно:

- Отдельная страница публикации `/posts/<id>/`.
- Удаление записи автором со страницей подтверждения (только POST).
- **Черновики**: кнопки «Опубликовать» и «Сохранить черновик»; черновик видит только автор, чужим он отдаёт 404.
- **Комментарии** для вошедших пользователей; удалить комментарий может его автор или автор публикации (проверка в представлении, только POST).
- Поиск по заголовкам и тексту (без учёта регистра, в том числе по-русски в SQLite).
- Пагинация (5 публикаций на страницу), страница автора `/authors/<username>/`, «Мои публикации и черновики».
- Отметка «изменено» у отредактированных записей, смена пароля, свои страницы 404 и 500.

## Страницы

| Страница | URL | Доступ |
|---|---|---|
| Главная со списком (+ поиск) | `/` | всем |
| Публикация | `/posts/<id>/` | всем; черновик - только автору |
| Создание публикации | `/posts/new/` | после входа |
| Редактирование | `/posts/<id>/edit/` | только автору |
| Удаление | `/posts/<id>/delete/` (GET - подтверждение, POST - удаление) | только автору |
| Публикации автора | `/authors/<username>/` | всем |
| Комментарий: добавить / удалить | `/posts/<id>/comments/`, `/comments/<id>/delete/` (POST) | после входа / автору комментария или записи |
| Вход, регистрация, выход | `/users/login/`, `/users/register/`, `/users/logout/` (POST) | всем |

## Права доступа

Проверка `{% if post.owner == user %}` в шаблоне только прячет ссылку. Настоящая защита - в представлении:

```python
post = get_object_or_404(BlogPost, id=post_id, owner=request.user)
```

Ручной переход к редактированию чужой записи и несуществующий ID дают 404. Поле `owner` в форму не входит,
поэтому подмена его в POST ничего не меняет. Комментарий удаляется только если текущий пользователь - его автор или автор публикации.

## Технологии

- Python 3.12, Django 5.2 LTS, django-bootstrap4 (Bootstrap 4.6)
- Gunicorn + WhiteNoise (статические файлы), Docker Compose
- SQLite на томе Docker по умолчанию или PostgreSQL через `DATABASE_URL`
- GitHub Actions: тесты на SQLite и PostgreSQL, `check --deploy` и запуск через `docker compose` при каждом push

## Структура

```
blog/            настройки проекта (settings.py читает всё из переменных окружения)
blogs/             основное приложение: модели, формы, представления, шаблоны, тесты
  management/commands/seed_demo.py   демо-данные для проверки
users/             регистрация, вход, POST-выход, смена пароля
  management/commands/ensure_admin.py   администратор из переменных окружения
templates/         base.html (навигация Bootstrap 4), страницы 404 и 500
static/css/        оформление поверх Bootstrap
Dockerfile, compose.yaml, start.sh   запуск в контейнере
render.yaml        бесплатное развёртывание на Render
```

## Локальный запуск

```sh
git clone https://github.com/njuk-s/rksi-blog.git
cd rksi-blog
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/. Без файла `.env` проект работает в режиме разработки (`DEBUG=True`, SQLite рядом с `manage.py`).

## Тесты

```sh
python manage.py check
python manage.py test
```

Что проверяют тесты:

- порядок публикаций на главной (новые первыми);
- пустое состояние;
- чтение без входа, ссылка редактирования только у автора;
- запрет создания без входа;
- автоматическое назначение автора, подмена `owner` в POST игнорируется;
- автор редактирует свою публикацию; чужая - 404 и не меняется;
- 404 для отсутствующего ID;
- регистрация и выход только через POST (в `users/tests.py`);
- удаление с подтверждением, черновики, комментарии и права на их удаление, поиск, пагинация;
- миграция автора назначает существующим записям существующего пользователя.

## Развёртывание на сервере через Docker Compose

Нужны Docker с плагином Compose и домен, направленный на сервер.

1. Получите код и создайте `.env` по образцу:

   ```sh
   git clone https://github.com/njuk-s/rksi-blog.git
   cd rksi-blog
   cp .env.example .env
   nano .env
   ```

   Обязательно задайте `DJANGO_SECRET_KEY` (сгенерировать: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   `DJANGO_DEBUG=False`, свой домен в `DJANGO_ALLOWED_HOSTS` и `https://домен` в `DJANGO_CSRF_TRUSTED_ORIGINS`.

2. Запустите:

   ```sh
   docker compose up -d --build
   docker compose ps
   docker compose logs --tail=100 web
   ```

   При каждом запуске контейнер сам применяет миграции (`start.sh` → `manage.py prestart`), статические файлы собираются при сборке образа.
   Если в `.env` заданы `DJANGO_SUPERUSER_USERNAME` и `DJANGO_SUPERUSER_PASSWORD`, администратор создаётся автоматически;
   иначе создайте его вручную:

   ```sh
   docker compose exec web python manage.py createsuperuser
   ```

3. Настройте HTTPS на обратном прокси. Пример для Nginx на том же сервере (`APP_BIND_IP=127.0.0.1`, `APP_PORT=8000`):

   ```nginx
   server {
       listen 80;
       server_name blog.example.ru;
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Затем выпустите сертификат: `sudo certbot --nginx -d blog.example.ru --redirect`.
   Для Nginx Proxy Manager на другом сервере укажите в `APP_BIND_IP` внутренний IP сервера с Django и используйте его с портом 8000 в Proxy Host.

База SQLite хранится на именованном томе `blog_data` и не пропадает при `docker compose up -d --build`.
Обновление: `git pull && docker compose up -d --build`.

## Переменные окружения

| Переменная | Обязательна | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | да, на сервере | Секретный ключ. При `DEBUG=False` проект не запустится с ключом по умолчанию |
| `DJANGO_DEBUG` | да, на сервере | `False` на сервере; по умолчанию `True` |
| `DJANGO_ALLOWED_HOSTS` | да | Домены через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | да, для HTTPS | `https://домен` через запятую |
| `SQLITE_PATH` | нет | Путь к базе SQLite; в Docker `/app/data/db.sqlite3` |
| `DATABASE_URL` | нет | PostgreSQL вместо SQLite, например `postgresql://user:pass@host/db?sslmode=require` |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | нет | Создать администратора при запуске |
| `SEED_DEMO`, `DEMO_PASSWORD` | нет | `SEED_DEMO=True` создаёт пользователей `anna` и `boris` с паролем `DEMO_PASSWORD` и демо-данные (один раз) |
| `DJANGO_SECURE_SSL_REDIRECT` | нет | `True` - перенаправлять HTTP на HTTPS средствами Django |
| `DJANGO_HSTS_SECONDS` | нет | Срок HSTS в секундах, по умолчанию 0 |
| `DJANGO_TIME_ZONE` | нет | Часовой пояс, по умолчанию `Europe/Moscow` |
| `APP_BIND_IP`, `APP_PORT` | нет | На каком адресе и порту Compose публикует контейнер (по умолчанию `127.0.0.1:8000`) |
| `PORT`, `WEB_CONCURRENCY`, `GUNICORN_THREADS` | нет | Порт, число процессов и потоков Gunicorn (по умолчанию 8000, 2 и 4) |

Файл `.env` в репозиторий не попадает (`.gitignore`), в репозитории лежит только образец `.env.example`.

## Бесплатное развёртывание без своего сервера

Работающая версия размещена бесплатно и не зависит от чьего-либо компьютера:

- **Render** (free web service) собирает образ по тому же `Dockerfile` и даёт домен с HTTPS;
- **Neon** (бесплатный PostgreSQL без срока действия) хранит данные: на бесплатном Render диск стирается
  при каждом перезапуске, поэтому SQLite там использовать нельзя - иначе публикации и пользователи пропадают;
- бесплатный Render усыпляет сервис после 15 минут без запросов, и первое открытие после сна занимает около 30 секунд.
  Workflow `.github/workflows/keepalive.yml` открывает `/healthz/` каждые 10 минут по будням с 8:00 до 17:00 по Москве,
  поэтому в рабочее время сайт открывается сразу. Круглосуточно будить нельзя: 750 бесплатных часов в месяц
  делятся на все сервисы аккаунта, и при их исчерпании Render отключает сервисы до конца месяца.
  `/healthz/` не обращается к базе, поэтому база Neon в простое засыпает и не тратит свой лимит.

Данные при засыпании и перезапуске не теряются: они в Neon, а не на диске контейнера.

Как повторить:

1. В [Neon](https://neon.com) создайте проект (регион Frankfurt) и скопируйте строку подключения (**Pooled connection**).
2. В [Render](https://render.com) выберите **New → Blueprint** и укажите этот репозиторий: настройки возьмутся из `render.yaml`.
3. Заполните `DATABASE_URL` (строка из Neon), `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` и `DEMO_PASSWORD`.
   `DJANGO_SECRET_KEY` Render сгенерирует сам.
4. После сборки сайт доступен по адресу `https://<имя-сервиса>.onrender.com`; миграции, администратор и демо-данные
   создаются при запуске контейнера.
5. Автодеплой: добавьте в репозиторий секрет `RENDER_API_KEY` (ключ из Render → Account Settings → API Keys)
   и переменную `RENDER_SERVICE_ID` (`srv-…` из адреса сервиса). Тогда после каждого push в `main` GitHub Actions
   сначала прогоняет тесты и сборку Docker, и только при успехе запускает деплой на Render.
