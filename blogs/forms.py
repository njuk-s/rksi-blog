from django import forms

from .models import BlogPost, Comment


class BlogPostForm(forms.ModelForm):
    """Автор меняет только заголовок и текст. Автора и дату задаёт сервер."""

    class Meta:
        model = BlogPost
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'О чём ваша публикация?'}),
            'text': forms.Textarea(attrs={'rows': 12}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Ваш комментарий'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000})}
