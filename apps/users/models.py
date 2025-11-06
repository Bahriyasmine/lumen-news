# from django.db import models
# from pgvector.django import VectorField
# from django.contrib.postgres.fields import ArrayField

# class User(models.Model):
#     username = models.CharField(max_length=100, unique=True)
#     email = models.EmailField(unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)

# class UserPreference(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferences')
#     domains = ArrayField(models.CharField(max_length=100), blank=True, default=list)
#     mental_state = models.CharField(max_length=50, blank=True, null=True)
#     min_sentiment = models.FloatField(blank=True, null=True)
#     preferences_text = models.TextField(blank=True, null=True)
#     embedding = VectorField(dimensions=768, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)


# apps/users/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorExtension, VectorField
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class UserPreference(models.Model):
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    domains = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    mental_state = models.CharField(max_length=50, blank=True)
    min_sentiment = models.FloatField(null=True, blank=True)
    preferences_text = models.TextField(blank=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)  # Requires pgvector
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user_profile.username}"