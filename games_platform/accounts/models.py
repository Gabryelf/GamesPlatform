from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('player', 'Игрок'),
        ('developer', 'Разработчик'),
        ('admin', 'Администратор'),
        ('owner', 'Владелец'),
    )

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='player',
        verbose_name='Тип пользователя'
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name='О себе')
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def is_owner(self):
        return self.user_type == 'owner'

    def is_admin(self):
        return self.user_type in ['admin', 'owner']

    def is_developer(self):
        return self.user_type in ['developer', 'admin', 'owner']

    def is_player(self):
        return self.user_type in ['player', 'developer', 'admin', 'owner']
