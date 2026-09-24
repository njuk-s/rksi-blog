"""
Добавляет автора публикации.

Существующим публикациям назначается существующий пользователь (первый
суперпользователь, иначе первый пользователь). Постоянного default=1 в модели
нет: поле сначала добавляется как необязательное, затем данные переносятся,
и только потом поле становится обязательным.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_owner(apps, schema_editor):
    BlogPost = apps.get_model('blogs', 'BlogPost')
    orphans = BlogPost.objects.filter(owner__isnull=True)
    if not orphans.exists():
        return
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    owner = (User.objects.filter(is_superuser=True).order_by('id').first()
             or User.objects.order_by('id').first())
    if owner is None:
        # Пользователей ещё нет: создаём неактивную учётную запись без пароля.
        owner = User.objects.create(username='legacy_author', is_active=False, password='!')
    orphans.update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blogs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(assign_existing_owner, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='blogpost',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
    ]
