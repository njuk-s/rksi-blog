"""Представления блога.

Читать опубликованные записи может любой посетитель. Изменять и удалять
запись может только её автор: объект достаётся запросом
get_object_or_404(BlogPost, id=post_id, owner=request.user), поэтому чужая
или несуществующая запись даёт 404 независимо от того, что показано в шаблоне.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import BlogPostForm, CommentForm
from .models import BlogPost, Comment

POSTS_PER_PAGE = 5


def paginate(request, queryset):
    return Paginator(queryset, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def post_list(queryset):
    return queryset.select_related('owner').annotate(comment_count=Count('comments')).order_by('-date_added')


def owned_post(request, post_id):
    return get_object_or_404(BlogPost, id=post_id, owner=request.user)


def index(request):
    """Главная: все опубликованные записи, новые первыми, с поиском."""
    posts = post_list(BlogPost.objects.published())
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(text__icontains=query))
    page = paginate(request, posts)
    return render(request, 'blogs/index.html', {'posts': page, 'page_obj': page, 'query': query})


def author(request, username):
    """Записи одного автора. Свои черновики автор тоже видит здесь."""
    author = get_object_or_404(get_user_model(), username=username)
    posts = BlogPost.objects.filter(owner=author)
    if request.user != author:
        posts = posts.published()
    page = paginate(request, post_list(posts))
    return render(request, 'blogs/author.html', {'author': author, 'posts': page, 'page_obj': page})


def post_detail(request, post_id):
    post = get_object_or_404(BlogPost.objects.visible_to(request.user).select_related('owner'), id=post_id)
    comments = post.comments.select_related('author', 'post')
    return render(request, 'blogs/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': CommentForm(),
        'can_delete': {c.id for c in comments if c.can_delete(request.user)},
    })


def apply_action(request, post):
    """Кнопка формы решает, опубликовать запись или оставить черновиком."""
    action = request.POST.get('action')
    if action == 'publish':
        post.is_published = True
    elif action == 'draft':
        post.is_published = False


@login_required
def post_new(request):
    if request.method != 'POST':
        form = BlogPostForm()
    else:
        form = BlogPostForm(data=request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.owner = request.user
            apply_action(request, new_post)
            new_post.save()
            if new_post.is_published:
                messages.success(request, 'Публикация опубликована.')
                return redirect('blogs:index')
            messages.info(request, 'Черновик сохранён. Его видите только вы.')
            return redirect('blogs:detail', post_id=new_post.id)
    return render(request, 'blogs/post_form.html', {'form': form, 'is_new': True})


@login_required
def post_edit(request, post_id):
    post = owned_post(request, post_id)
    if request.method != 'POST':
        form = BlogPostForm(instance=post)
    else:
        form = BlogPostForm(instance=post, data=request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            apply_action(request, post)
            post.save()
            messages.success(request, 'Изменения сохранены.')
            return redirect('blogs:detail', post_id=post.id)
    return render(request, 'blogs/post_form.html', {'form': form, 'post': post, 'is_new': False})


@login_required
@require_http_methods(['GET', 'POST'])
def post_delete(request, post_id):
    """GET показывает подтверждение, удаление только через POST."""
    post = owned_post(request, post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, f'Публикация «{post}» удалена.')
        return redirect('blogs:index')
    return render(request, 'blogs/post_confirm_delete.html', {'post': post})


@login_required
@require_POST
def comment_add(request, post_id):
    post = get_object_or_404(BlogPost.objects.published(), id=post_id)
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        messages.success(request, 'Комментарий добавлен.')
        return redirect(f'{post.get_absolute_url()}#comment-{comment.id}')
    messages.error(request, 'Комментарий не может быть пустым или длиннее 2000 символов.')
    return redirect(f'{post.get_absolute_url()}#comments')


@login_required
@require_POST
def comment_delete(request, comment_id):
    """Удалить комментарий может его автор или автор публикации."""
    comment = get_object_or_404(
        Comment.objects.filter(Q(author=request.user) | Q(post__owner=request.user)),
        id=comment_id,
    )
    post = comment.post
    comment.delete()
    messages.success(request, 'Комментарий удалён.')
    return redirect(f'{post.get_absolute_url()}#comments')
