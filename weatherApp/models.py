from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class CaseInsensitiveUserManager(UserManager):
    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)

    async def aget_by_natural_key(self, username):
        return await self.aget(username__iexact=username)


class User(AbstractUser):
    objects = CaseInsensitiveUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('username'),
                name='unique_username_case_insensitive',
            ),
        ]


class SavedCity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_cities',
    )
    city_id = models.BigIntegerField()
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=2, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'country', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'city_id'],
                name='unique_saved_city_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.name}, {self.country}' if self.country else self.name
