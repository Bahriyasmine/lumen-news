# config/views.py

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

@login_required
def home(request):
    """
    Homepage view: requires login.
    Redirects to signin page if user is not authenticated.
    """
    if not request.user.is_authenticated:
        return redirect('signin')
    return render(request, 'home.html')

@ensure_csrf_cookie
def signup_page(request):
    """
    Render the signup page.
    """
    return render(request, 'signup.html')

def signin_page(request):
    """
    Render the signin page.
    """
    return render(request, 'signin.html')

def Onboarding(request):
    """
    Render the onboarding page.
    """
    return render(request, 'onboarding.html')
