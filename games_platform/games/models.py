from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

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

    def get_average_rating(self):
        """Средний рейтинг игры"""
        if hasattr(self, 'stats'):
            return self.stats.get_average_rating()
        return 0

    def get_rating_count(self):
        """Количество оценок"""
        if hasattr(self, 'stats'):
            return self.stats.get_rating_count()
        return 0

    def get_view_count(self):
        """Количество просмотров"""
        if hasattr(self, 'stats'):
            return self.stats.views
        return 0

    def get_play_count(self):
        """Количество запусков"""
        if hasattr(self, 'stats'):
            return self.stats.play_count
        return 0

    def get_comment_count(self):
        """Количество комментариев"""
        return self.comments.count()

    def increment_views(self):
        """Увеличить счетчик просмотров"""
        if not hasattr(self, 'stats'):
            GameStat.objects.create(game=self)
        self.stats.increment_views()

    def increment_play_count(self):
        """Увеличить счетчик запусков"""
        if not hasattr(self, 'stats'):
            GameStat.objects.create(game=self)
        self.stats.increment_play_count()

    def user_rating(self, user):
        """Получить оценку пользователя для этой игры"""
        if user.is_authenticated:
            try:
                return self.ratings.get(user=user).rating
            except GameRating.DoesNotExist:
                return 0
        return 0


class GameRating(models.Model):
    """Рейтинг игры от пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='game_ratings',
        verbose_name='Пользователь'
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Игра'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оценки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        unique_together = ['user', 'game']
        verbose_name = 'Оценка игры'
        verbose_name_plural = 'Оценки игр'

    def __str__(self):
        return f"{self.user.username}: {self.rating} звезд для {self.game.title}"


class Comment(models.Model):
    """Комментарий к игре"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пользователь'
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Игра'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_edited = models.BooleanField(default=False, verbose_name='Отредактирован')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f"Комментарий от {self.user.username} к игре {self.game.title}"


class GameStat(models.Model):
    """Статистика игры (просмотры, лайки)"""
    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Игра'
    )
    views = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    likes = models.PositiveIntegerField(default=0, verbose_name='Лайки')
    dislikes = models.PositiveIntegerField(default=0, verbose_name='Дизлайки')
    play_count = models.PositiveIntegerField(default=0, verbose_name='Количество запусков')
    last_played = models.DateTimeField(null=True, blank=True, verbose_name='Последний запуск')

    class Meta:
        verbose_name = 'Статистика игры'
        verbose_name_plural = 'Статистика игр'

    def __str__(self):
        return f"Статистика для {self.game.title}"

    def increment_views(self):
        self.views += 1
        self.save()

    def increment_play_count(self):
        self.play_count += 1
        self.last_played = timezone.now()
        self.save()

    def get_average_rating(self):
        ratings = self.game.ratings.all()
        if ratings:
            return round(sum(r.rating for r in ratings) / len(ratings), 1)
        return 0

    def get_rating_count(self):
        return self.game.ratings.count()
