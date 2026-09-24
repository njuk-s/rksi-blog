"""Модели блога: публикация и комментарии к ней."""
from django.conf import settings
from django.db import models
from django.urls import reverse


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def visible_to(self, user):
        """Опубликованные записи плюс черновики самого пользователя."""
        if user.is_authenticated:
            return self.filter(models.Q(is_published=True) | models.Q(owner=user))
        return self.published()


class BlogPost(models.Model):
    """Публикация в блоге."""
    title = models.CharField('заголовок', max_length=200)
    text = models.TextField('текст')
    date_added = models.DateTimeField('дата публикации', auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='posts', verbose_name='автор')
    date_modified = models.DateTimeField('изменена', auto_now=True)
    is_published = models.BooleanField(
        'опубликована', default=True,
        help_text='Черновик видит только автор.',
    )

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ['-date_added']
        verbose_name = 'публикация'
        verbose_name_plural = 'публикации'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blogs:detail', args=[self.id])

    @property
    def was_edited(self):
        return (self.date_modified - self.date_added).total_seconds() > 60


class Comment(models.Model):
    """Комментарий к публикации."""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments',
                             verbose_name='публикация')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='comments', verbose_name='автор')
    text = models.TextField('комментарий', max_length=2000)
    date_added = models.DateTimeField('добавлен', auto_now_add=True)

    class Meta:
        ordering = ['date_added']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author}: {self.text[:40]}'

    def can_delete(self, user):
        """Удалить комментарий может его автор или автор публикации."""
        return user.is_authenticated and user.id in (self.author_id, self.post.owner_id)
