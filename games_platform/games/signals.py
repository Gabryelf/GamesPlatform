from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Game, GameStat


@receiver(post_save, sender=Game)
def create_game_stat(sender, instance, created, **kwargs):
    """Автоматически создаем статистику для новой игры"""
    if created:
        GameStat.objects.create(game=instance)


@receiver(post_save, sender=Game)
def save_game_stat(sender, instance, **kwargs):
    """Сохраняем статистику при сохранении игры"""
    if hasattr(instance, 'stats'):
        instance.stats.save()
