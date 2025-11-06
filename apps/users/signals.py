# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # DO NOT pass username/email — they are in auth.User
        profile = UserProfile.objects.create(user=instance)
        UserPreference.objects.create(user_profile=profile)