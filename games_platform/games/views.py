from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Game
from .forms import GameForm


def game_list(request):
    # Для обычных пользователей показываем только одобренные игры
    if request.user.is_authenticated and request.user.is_admin():
        games = Game.objects.all()
    else:
        games = Game.objects.filter(status='approved')

    return render(request, 'games/game_list.html', {'games': games})


def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)

    # Проверяем доступ
    if game.status != 'approved' and not request.user.is_admin():
        if request.user != game.developer:
            messages.error(request, 'Эта игра еще не прошла модерацию')
            return redirect('game_list')

    return render(request, 'games/game_detail.html', {'game': game})


@login_required
def game_create(request):
    if not request.user.is_developer():
        messages.error(request, 'Только разработчики могут загружать игры')
        return redirect('game_list')

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
            game = form.save(commit=False)
            game.developer = request.user
            game.save()
            messages.success(request, 'Игра успешно загружена и отправлена на модерацию')
            return redirect('game_detail', pk=game.pk)
    else:
        form = GameForm()

    return render(request, 'games/game_form.html', {
        'form': form,
        'title': 'Загрузить новую игру'
    })


@login_required
def game_edit(request, pk):
    game = get_object_or_404(Game, pk=pk)

    if not game.can_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этой игры')
        return redirect('game_detail', pk=game.pk)

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES, instance=game)
        if form.is_valid():
            # Если игра редактируется, снова отправляем на модерацию
            if game.is_approved():
                game.status = 'pending'
                messages.info(request, 'Игра отправлена на повторную модерацию')

            form.save()
            messages.success(request, 'Игра успешно обновлена')
            return redirect('game_detail', pk=game.pk)
    else:
        form = GameForm(instance=game)

    return render(request, 'games/game_form.html', {
        'form': form,
        'title': 'Редактировать игру',
        'game': game
    })


@login_required
def game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)

    if not game.can_delete(request.user):
        messages.error(request, 'У вас нет прав для удаления этой игры')
        return redirect('game_detail', pk=game.pk)

    if request.method == 'POST':
        game.delete()
        messages.success(request, 'Игра успешно удалена')
        return redirect('game_list')

    return render(request, 'games/game_confirm_delete.html', {'game': game})


@login_required
def moderation_list(request):
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('game_list')

    pending_games = Game.objects.filter(status='pending')
    return render(request, 'games/moderation_list.html', {
        'pending_games': pending_games
    })


@login_required
def moderate_game(request, pk, action):
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('game_list')

    game = get_object_or_404(Game, pk=pk)

    if action == 'approve':
        game.status = 'approved'
        game.published_at = timezone.now()
        game.save()
        messages.success(request, f'Игра "{game.title}" одобрена')
    elif action == 'reject':
        game.status = 'rejected'
        game.save()
        messages.warning(request, f'Игра "{game.title}" отклонена')

    return redirect('moderation_list')
