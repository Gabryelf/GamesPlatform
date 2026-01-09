from .models import Game


def moderation_count(request):
    if request.user.is_authenticated and request.user.is_admin():
        pending_count = Game.objects.filter(status='pending').count()
        return {'pending_games_count': pending_count}
    return {'pending_games_count': 0}
