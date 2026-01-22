from django import forms
from blog.models import Content, Tag, TagGroup


FORM_INPUT_CLASS = 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'


class TagGroupForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = TagGroup
        fields = ['name']
        labels = {
            'name': 'Название группы',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': FORM_INPUT_CLASS,
                'placeholder': 'Например: Месяц практики',
            }),
        }


class TagForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Tag
        fields = ['name', 'group']
        labels = {
            'name': 'Название тега',
            'group': 'Группа',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': FORM_INPUT_CLASS,
                'placeholder': 'Например: Первый месяц',
            }),
            'group': forms.Select(attrs={
                'class': FORM_INPUT_CLASS,
            }),
        }


class ContentForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Content
        fields = ['title', 'description', 'content_type', 'category', 'tags', 'thumbnail', 'video_file', 'duration']
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'content_type': 'Тип контента',
            'category': 'Категория',
            'tags': 'Теги',
            'thumbnail': 'Превью',
            'video_file': 'Видеофайл',
            'duration': 'Длительность',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': FORM_INPUT_CLASS,
                'placeholder': 'Название видео или фото',
            }),
            'description': forms.Textarea(attrs={
                'class': FORM_INPUT_CLASS,
                'rows': 4,
                'placeholder': 'Описание контента',
            }),
            'content_type': forms.Select(attrs={
                'class': FORM_INPUT_CLASS,
            }),
            'category': forms.Select(attrs={
                'class': FORM_INPUT_CLASS,
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'duration': forms.TextInput(attrs={
                'class': FORM_INPUT_CLASS,
                'placeholder': '10:30',
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': FORM_INPUT_CLASS,
            }),
            'video_file': forms.ClearableFileInput(attrs={
                'class': FORM_INPUT_CLASS,
            }),
        }
