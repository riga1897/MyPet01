from django import forms
from blog.models import Content


class ContentForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Content
        fields = ['title', 'description', 'content_type', 'category', 'thumbnail', 'video_file', 'duration']
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'content_type': 'Тип контента',
            'category': 'Категория',
            'thumbnail': 'Превью',
            'video_file': 'Видеофайл',
            'duration': 'Длительность',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': 'Название видео или фото',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
                'rows': 4,
                'placeholder': 'Описание контента',
            }),
            'content_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': '10:30',
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
            }),
            'video_file': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary',
            }),
        }
