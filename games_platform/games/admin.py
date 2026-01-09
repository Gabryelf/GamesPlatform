from django.contrib import admin
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'developer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'developer__username']
    list_editable = ['status']
    actions = ['approve_games', 'reject_games']

    def approve_games(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, 'Выбранные игры одобрены')

    approve_games.short_description = 'Одобрить выбранные игры'

    def reject_games(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, 'Выбранные игры отклонены')

    reject_games.short_description = 'Отклонить выбранные игры'
