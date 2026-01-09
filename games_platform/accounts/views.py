from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import CustomUserCreationForm, LoginForm, UserEditForm, UserAdminCreateForm
from .models import CustomUser


def home(request):
    context = {}

    if request.user.is_authenticated:
        Game = apps.get_model('games', 'Game')
        recent_games = Game.objects.filter(status='approved').order_by('-created_at')[:3]
        context['recent_games'] = recent_games

    return render(request, 'accounts/home.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Первый зарегистрированный пользователь становится владельцем
            if CustomUser.objects.count() == 1:
                user.user_type = 'owner'
                user.save()

            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def user_list(request):
    """Список всех пользователей (только для админов и владельца)"""
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('home')

    users = CustomUser.objects.all().order_by('-date_joined')

    # Поиск пользователей
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Фильтрация по типу пользователя
    user_type = request.GET.get('type', '')
    if user_type:
        users = users.filter(user_type=user_type)

    # Статистика
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    developers_count = CustomUser.objects.filter(user_type='developer').count()
    admins_count = CustomUser.objects.filter(user_type__in=['admin', 'owner']).count()

    context = {
        'users': users,
        'search_query': search_query,
        'user_type_filter': user_type,
        'user_type_choices': CustomUser.USER_TYPE_CHOICES,
        'total_users': total_users,
        'active_users': active_users,
        'developers_count': developers_count,
        'admins_count': admins_count,
    }

    return render(request, 'accounts/user_list.html', context)


@login_required
def user_detail(request, pk):
    """Детальная информация о пользователе"""
    user = get_object_or_404(CustomUser, pk=pk)

    # Проверяем права доступа
    if not user.can_be_edited_by(request.user) and request.user != user:
        messages.error(request, 'У вас нет прав для просмотра этого профиля')
        return redirect('home')

    # Получаем игры пользователя
    Game = apps.get_model('games', 'Game')
    if user.is_developer() or user.is_admin():
        user_games = Game.objects.filter(developer=user)
    else:
        user_games = None

    context = {
        'profile_user': user,
        'user_games': user_games,
    }

    return render(request, 'accounts/user_detail.html', context)


@login_required
def user_edit(request, pk):
    """Редактирование пользователя"""
    user = get_object_or_404(CustomUser, pk=pk)

    # Проверяем права доступа
    if not user.can_be_edited_by(request.user):
        messages.error(request, 'У вас нет прав для редактирования этого пользователя')
        return redirect('user_detail', pk=user.pk)

    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=user, request_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('user_detail', pk=user.pk)
    else:
        form = UserEditForm(instance=user, request_user=request.user)

    context = {
        'form': form,
        'profile_user': user,
        'is_editing_self': request.user == user,
    }

    return render(request, 'accounts/user_edit.html', context)


@login_required
def user_create_admin(request):
    """Создание пользователя администратором"""
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('home')

    if request.method == 'POST':
        form = UserAdminCreateForm(request.POST, request_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь {user.username} успешно создан')
            return redirect('user_detail', pk=user.pk)
    else:
        form = UserAdminCreateForm(request_user=request.user)

    context = {
        'form': form,
        'title': 'Создание пользователя',
    }

    return render(request, 'accounts/user_form_admin.html', context)


@login_required
def user_toggle_active(request, pk):
    """Блокировка/разблокировка пользователя"""
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('home')

    user = get_object_or_404(CustomUser, pk=pk)

    # Проверяем, можно ли изменять этого пользователя
    if not user.can_be_edited_by(request.user):
        messages.error(request, 'У вас нет прав для блокировки этого пользователя')
        return redirect('user_detail', pk=user.pk)

    # Нельзя блокировать самого себя
    if user == request.user:
        messages.error(request, 'Вы не можете заблокировать себя')
        return redirect('user_detail', pk=user.pk)

    user.is_active = not user.is_active
    user.save()

    action = "разблокирован" if user.is_active else "заблокирован"
    messages.success(request, f'Пользователь {user.username} {action}')

    return redirect('user_detail', pk=user.pk)


@login_required
def user_delete(request, pk):
    """Удаление пользователя"""
    if not request.user.is_admin():
        messages.error(request, 'Доступ только для администраторов')
        return redirect('home')

    user = get_object_or_404(CustomUser, pk=pk)

    # Проверяем, можно ли удалить этого пользователя
    if not user.can_be_deleted_by(request.user):
        messages.error(request, 'У вас нет прав для удаления этого пользователя')
        return redirect('user_detail', pk=user.pk)

    # Нельзя удалить самого себя
    if user == request.user:
        messages.error(request, 'Вы не можете удалить себя')
        return redirect('user_detail', pk=user.pk)

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Пользователь {username} удален')
        return redirect('user_list')

    # Получаем количество игр пользователя для предупреждения
    Game = apps.get_model('games', 'Game')
    game_count = Game.objects.filter(developer=user).count()

    context = {
        'user_to_delete': user,
        'game_count': game_count,
    }

    return render(request, 'accounts/user_confirm_delete.html', context)
