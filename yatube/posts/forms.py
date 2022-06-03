from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка'
        }

        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа для поста',
            'image': 'Картинка для поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

        labels = {
            'text': 'Текст',
        }

        help_texts = {
            'text': 'Текст комментария',
        }
