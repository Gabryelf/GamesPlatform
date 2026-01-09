from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Game(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На проверке'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )

    title = models.CharField(max_length=200, verbose_name='Название игры')
    description = models.TextField(verbose_name='Описание игры')
    developer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='games',
        verbose_name='Разработчик'
    )
    html_file = models.FileField(
        upload_to='games/html/',
        verbose_name='HTML файл игры'
    )
    thumbnail = models.ImageField(
        upload_to='games/thumbnails/',
        null=True,
        blank=True,
        verbose_name='Превью игры'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус модерации'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def is_approved(self):
        return self.status == 'approved'

    def can_edit(self, user):
        return user == self.developer or user.is_admin()

    def can_delete(self, user):
        if user.is_owner():
            return True
        elif user.is_admin():
            return user != self.developer  # Админ не может удалять свои игры как админ
        else:
            return user == self.developer
