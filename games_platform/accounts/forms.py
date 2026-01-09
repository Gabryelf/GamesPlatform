from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор типа пользователя для обычной регистрации
        self.fields['user_type'].choices = [
            ('player', 'Игрок'),
            ('developer', 'Разработчик'),
        ]
        # Делаем поля обязательными
        self.fields['email'].required = True


class LoginForm(forms.Form):
    username = forms.CharField(label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class UserEditForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'bio', 'avatar', 'is_active')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Убираем поле пароля
        if 'password' in self.fields:
            del self.fields['password']

        # Ограничиваем выбор типа пользователя в зависимости от прав
        if self.request_user:
            if self.request_user.is_owner():
                # Владелец может назначать любые роли
                self.fields['user_type'].choices = CustomUser.USER_TYPE_CHOICES
            elif self.request_user.is_admin():
                # Админ может назначать только игроков и разработчиков
                self.fields['user_type'].choices = [
                    ('player', 'Игрок'),
                    ('developer', 'Разработчик'),
                ]
            else:
                # Обычные пользователи не могут менять тип
                del self.fields['user_type']


class UserAdminCreateForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор типа пользователя
        if self.request_user:
            if self.request_user.is_owner():
                self.fields['user_type'].choices = [
                    ('player', 'Игрок'),
                    ('developer', 'Разработчик'),
                    ('admin', 'Администратор'),
                ]
            elif self.request_user.is_admin():
                self.fields['user_type'].choices = [
                    ('player', 'Игрок'),
                    ('developer', 'Разработчик'),
                ]

        self.fields['email'].required = True
