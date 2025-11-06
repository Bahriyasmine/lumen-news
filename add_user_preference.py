# add_user_preference.py
from django.conf import settings
from django.db import connection
import os

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.users.models import UserProfile, UserPreference

def main():
    print("Adding UserPreference for UserProfile(id=1)...\n")

    try:
        # Get the profile
        profile = UserProfile.objects.get(id=1)
        user = profile.user
        print(f"Found User: {user.username} (ID: {user.id})")
        print(f"UserProfile ID: {profile.id}\n")

        # Create preference
        pref, created = UserPreference.objects.get_or_create(
            user_profile=profile,
            defaults={
                'domains': ['sport', 'tech'],
                'mental_state': 'curious',
                'min_sentiment': 0.3,
                'preferences_text': 'I love sports and football news.',
                'embedding': None,
            }
        )

        if created:
            print("SUCCESS: UserPreference created!")
        else:
            print("INFO: UserPreference already exists. Updating...")
            pref.domains = ['sport', 'tech']
            pref.mental_state = 'curious'
            pref.min_sentiment = 0.3
            pref.preferences_text = 'I love sports and football news.'
            pref.save()
            print("SUCCESS: UserPreference updated!")

        # Verify
        print("\nVERIFICATION:")
        print(f"   ID: {pref.id}")
        print(f"   Domains: {pref.domains}")
        print(f"   Mental State: {pref.mental_state}")
        print(f"   Min Sentiment: {pref.min_sentiment}")
        print(f"   Text: {pref.preferences_text}")

    except UserProfile.DoesNotExist:
        print("ERROR: UserProfile with id=1 not found!")
        print("Run: SELECT * FROM users_userprofile;")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()