from django.contrib import admin
from django.urls import path, include
from config import views  # your main views
from apps.users.views import save_preferences  # <-- import this if defined in users app
from apps.users.views import OnboardingView
from apps.users.views import save_preferences
urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', include('apps.feed.urls')),  # Feed URLs
    path('', include(('apps.feed.urls', 'feed'), namespace='feed')),  # Add namespace here
    #--------------------------------
    path('home/', views.home, name='home'),
    path('home/Signup', views.signup_page, name='signup'),
    path('home/Login', views.signin_page, name='signin'),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),
    path('api/auth/', include('dj_rest_auth.urls')), # Handles login, logout, password reset, etc.
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')), # Handles registration
    path('accounts/', include('allauth.urls')),  # ← This includes social login URLs
    path('api/preferences/save/', save_preferences, name='save_preferences'),
]
