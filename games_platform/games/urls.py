from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.game_list, name='game_list'),
    path('games/create/', views.game_create, name='game_create'),
    path('games/<int:pk>/', views.game_detail, name='game_detail'),
    path('games/<int:pk>/edit/', views.game_edit, name='game_edit'),
    path('games/<int:pk>/delete/', views.game_delete, name='game_delete'),

    # Комментарии и рейтинги
    path('games/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_pk>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_pk>/delete/', views.delete_comment, name='delete_comment'),
    path('games/<int:pk>/rate/', views.rate_game, name='rate_game'),
    path('games/<int:pk>/toggle-like/', views.toggle_like, name='toggle_like'),
    path('games/<int:pk>/increment-play/', views.increment_play_count, name='increment_play_count'),

    # Модерация
    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:pk>/<str:action>/', views.moderate_game, name='moderate_game'),

    # Популярные игры
    path('games/popular/', views.popular_games, name='popular_games'),
    path('games/best-rated/', views.best_rated_games, name='best_rated_games'),
]
