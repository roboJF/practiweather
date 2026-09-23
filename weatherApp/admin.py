from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SavedCity, User


@admin.register(User)
class WeatherUserAdmin(UserAdmin):
    pass


@admin.register(SavedCity)
class SavedCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'user', 'created_at')
    list_filter = ('country',)
    search_fields = ('name', 'user__username')
