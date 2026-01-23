from typing import Any, cast

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from blog.models import Content, Tag, TagGroup
from blog.services import generate_hashed_filename


FORM_INPUT_CLASS = 'w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'
CHECKBOX_CLASS = 'w-4 h-4 text-primary border-border rounded focus:ring-primary'


class TagGroupForm(forms.ModelForm):  # type: ignore[type-arg]
    select_all = forms.BooleanField(
        required=False,
        label='Выбрать все категории',
        widget=forms.CheckboxInput(attrs={
            'class': CHECKBOX_CLASS,
            'id': 'select-all-categories',
        }),
    )

    class Meta:
        model = TagGroup
        fields = ['name', 'categories']
        labels = {
            'name': 'Название группы',
            'categories': 'Категории',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': FORM_INPUT_CLASS,
                'placeholder': 'Например: Месяц практики',
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2 category-checkboxes',
            }),
        }
        help_texts = {
            'categories': 'Оставьте пустым для применения ко всем категориям',
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        from blog.models import Category
        all_category_count = Category.objects.count()
        if self.instance and self.instance.pk:
            selected_count = self.instance.categories.count()
            self.fields['select_all'].initial = (
                selected_count == all_category_count and all_category_count > 0
            )


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
        fields = ['title', 'description', 'content_type', 'categories', 'tags', 'thumbnail', 'video_file']
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'content_type': 'Тип контента',
            'categories': 'Категории',
            'tags': 'Теги',
            'thumbnail': 'Превью',
            'video_file': 'Файл',
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
            'content_type': forms.RadioSelect(attrs={
                'class': 'space-y-2',
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': FORM_INPUT_CLASS,
            }),
            'video_file': forms.ClearableFileInput(attrs={
                'class': FORM_INPUT_CLASS,
            }),
        }

    def clean_video_file(self) -> InMemoryUploadedFile | TemporaryUploadedFile | None:
        """Add MD5 hash to uploaded video filename."""
        video_file = self.cleaned_data.get('video_file')
        if video_file and isinstance(video_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            hashed_name, _ = generate_hashed_filename(video_file)
            video_file.name = hashed_name
        return video_file

    def save(self, commit: bool = True) -> Content:
        instance: Content = cast(Content, super().save(commit=False))
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance
