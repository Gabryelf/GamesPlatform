from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from django.http import JsonResponse
from .models import Game, Comment, GameRating, GameStat
from .forms import GameForm, CommentForm, RatingForm


def game_list(request):
    # Для обычных пользователей показываем только одобренные игры
    if request.user.is_authenticated and request.user.is_admin():
        games = Game.objects.all()
    else:
        games = Game.objects.filter(status='approved')

    return render(request, 'games/game_list.html', {'games': games})


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


def game_detail(request, pk):
    """Детальная информация об игре с просмотрами"""
    game = get_object_or_404(Game, pk=pk)

    # Проверяем доступ
    if game.status != 'approved' and not request.user.is_authenticated:
        messages.error(request, 'Эта игра еще не прошла модерацию')
        return redirect('game_list')

    if game.status != 'approved' and request.user.is_authenticated and not request.user.is_admin():
        if request.user != game.developer:
            messages.error(request, 'Эта игра еще не прошла модерацию')
            return redirect('game_list')

    # Увеличиваем счетчик просмотров
    game.increment_views()

    # Получаем комментарии
    comments = game.comments.all()

    # Получаем форму для комментария
    comment_form = CommentForm()

    # Получаем форму для рейтинга
    rating_form = RatingForm()
    user_rating = 0

    if request.user.is_authenticated:
        # Получаем оценку пользователя, если есть
        try:
            user_rating_obj = GameRating.objects.get(user=request.user, game=game)
            rating_form = RatingForm(instance=user_rating_obj)
            user_rating = user_rating_obj.rating
        except GameRating.DoesNotExist:
            pass

    # Передаем контекст с can_edit и can_delete
    context = {
        'game': game,
        'comments': comments,
        'comment_form': comment_form,
        'rating_form': rating_form,
        'user_rating': user_rating,
        'average_rating': game.get_average_rating(),
        'rating_count': game.get_rating_count(),
        'can_edit': game.can_edit(request.user) if request.user.is_authenticated else False,
        'can_delete': game.can_delete(request.user) if request.user.is_authenticated else False,
    }

    return render(request, 'games/game_detail.html', context)


@login_required
def add_comment(request, pk):
    """Добавление комментария к игре"""
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.game = game
            comment.save()
            messages.success(request, 'Комментарий добавлен')

    return redirect('game_detail', pk=game.pk)


@login_required
def edit_comment(request, comment_pk):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, pk=comment_pk)

    # Проверяем, что пользователь является автором комментария
    if comment.user != request.user and not request.user.is_admin():
        messages.error(request, 'Вы не можете редактировать этот комментарий')
        return redirect('game_detail', pk=comment.game.pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Комментарий отредактирован')

    return redirect('game_detail', pk=comment.game.pk)


@login_required
def delete_comment(request, comment_pk):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, pk=comment_pk)
    game_pk = comment.game.pk

    # Проверяем права на удаление
    can_delete = (
            comment.user == request.user or  # Автор комментария
            request.user.is_admin() or  # Администратор
            request.user == comment.game.developer  # Разработчик игры
    )

    if not can_delete:
        messages.error(request, 'У вас нет прав для удаления этого комментария')
        return redirect('game_detail', pk=game_pk)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий удален')

    return redirect('game_detail', pk=game_pk)


@login_required
def rate_game(request, pk):
    """Оценка игры"""
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        # Проверяем, есть ли уже оценка от пользователя
        try:
            rating_obj = GameRating.objects.get(user=request.user, game=game)
            form = RatingForm(request.POST, instance=rating_obj)
        except GameRating.DoesNotExist:
            form = RatingForm(request.POST)

        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.game = game
            rating.save()
            messages.success(request, 'Спасибо за оценку!')

    return redirect('game_detail', pk=game.pk)


@login_required
def toggle_like(request, pk):
    """Лайк/дизлайк игры (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        game = get_object_or_404(Game, pk=pk)
        action = request.POST.get('action')

        # Создаем статистику, если ее нет
        if not hasattr(game, 'stats'):
            GameStat.objects.create(game=game)

        if action == 'like':
            game.stats.likes += 1
        elif action == 'dislike':
            game.stats.dislikes += 1

        game.stats.save()

        return JsonResponse({
            'success': True,
            'likes': game.stats.likes,
            'dislikes': game.stats.dislikes,
        })

    return JsonResponse({'success': False}, status=400)


def popular_games(request):
    """Самые популярные игры"""
    games = Game.objects.filter(status='approved')

    # Сортируем по просмотрам (можно добавить другие критерии)
    games_with_stats = []
    for game in games:
        games_with_stats.append({
            'game': game,
            'views': game.get_view_count(),
            'rating': game.get_average_rating(),
            'plays': game.get_play_count(),
        })

    # Сортируем по просмотрам
    games_with_stats.sort(key=lambda x: x['views'], reverse=True)

    context = {
        'games': games_with_stats[:10],  # Топ-10
        'title': 'Популярные игры',
    }

    return render(request, 'games/popular_games.html', context)


def best_rated_games(request):
    """Лучшие игры по рейтингу"""
    games = Game.objects.filter(status='approved')

    # Фильтруем игры с достаточным количеством оценок
    rated_games = []
    for game in games:
        rating = game.get_average_rating()
        rating_count = game.get_rating_count()
        if rating_count >= 3:  # Минимум 3 оценки
            rated_games.append({
                'game': game,
                'rating': rating,
                'rating_count': rating_count,
                'views': game.get_view_count(),
            })

    # Сортируем по рейтингу
    rated_games.sort(key=lambda x: x['rating'], reverse=True)

    context = {
        'games': rated_games[:10],  # Топ-10
        'title': 'Лучшие игры по рейтингу',
    }

    return render(request, 'games/best_rated_games.html', context)


@login_required
def increment_play_count(request, pk):
    """Увеличить счетчик запусков игры (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        game = get_object_or_404(Game, pk=pk)
        game.increment_play_count()

        return JsonResponse({
            'success': True,
            'play_count': game.get_play_count(),
        })

    return JsonResponse({'success': False}, status=400)
