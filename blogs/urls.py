"""Маршруты приложения blogs."""
from django.urls import path

from . import views

app_name = 'blogs'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/new/', views.post_new, name='new'),
    path('posts/<int:post_id>/', views.post_detail, name='detail'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='edit'),
    path('posts/<int:post_id>/delete/', views.post_delete, name='delete'),
    path('posts/<int:post_id>/comments/', views.comment_add, name='comment_add'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('authors/<str:username>/', views.author, name='author'),
]
