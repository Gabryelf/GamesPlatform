from django import forms
from .models import Game


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'description', 'html_file', 'thumbnail']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_html_file(self):
        html_file = self.cleaned_data.get('html_file')
        if html_file:
            # Проверяем расширение файла
            if not html_file.name.endswith('.html'):
                raise forms.ValidationError('Файл должен иметь расширение .html')

            # Проверяем размер файла (макс 5MB)
            if html_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 5MB')

        return html_file
