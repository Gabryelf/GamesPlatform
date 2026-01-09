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
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP последнего входа')

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

    def can_be_deleted_by(self, user):
        """Определяет, может ли текущий пользователь удалить этого пользователя"""
        if user.is_owner():
            # Владелец может удалить любого, кроме себя
            return self != user
        elif user.is_admin():
            # Админ может удалить только игроков и разработчиков
            return self.user_type in ['player', 'developer']
        return False

    def can_be_edited_by(self, user):
        """Определяет, может ли текущий пользователь редактировать этого пользователя"""
        if user.is_owner():
            return True
        elif user.is_admin():
            # Админ может редактировать только игроков и разработчиков
            return self.user_type in ['player', 'developer']
        elif user == self:
            # Пользователь может редактировать себя
            return True
        return False
