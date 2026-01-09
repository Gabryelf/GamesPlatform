from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.game_list, name='game_list'),
    path('games/create/', views.game_create, name='game_create'),
    path('games/<int:pk>/', views.game_detail, name='game_detail'),
    path('games/<int:pk>/edit/', views.game_edit, name='game_edit'),
    path('games/<int:pk>/delete/', views.game_delete, name='game_delete'),
    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:pk>/<str:action>/', views.moderate_game, name='moderate_game'),
]
