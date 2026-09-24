from django.contrib import admin
from django.db.models import Count

from .models import BlogPost, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'text', 'date_added')
    readonly_fields = ('date_added',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'date_added', 'is_published', 'comment_count')
    list_filter = ('is_published', 'date_added', 'owner')
    search_fields = ('title', 'text')
    list_select_related = ('owner',)
    date_hierarchy = 'date_added'
    readonly_fields = ('date_added', 'date_modified')
    inlines = [CommentInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_comments=Count('comments'))

    @admin.display(description='комментариев', ordering='_comments')
    def comment_count(self, obj):
        return obj._comments

    def get_changeform_initial_data(self, request):
        # Новая публикация в админке по умолчанию принадлежит тому, кто её создаёт.
        return {'owner': request.user.pk}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'post', 'author', 'date_added')
    list_filter = ('date_added', 'author')
    search_fields = ('text', 'post__title', 'author__username')
    list_select_related = ('post', 'author')
