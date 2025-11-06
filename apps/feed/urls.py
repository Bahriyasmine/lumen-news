from django.urls import path
from . import views

from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Public pages (NO login required)
    path('contact.html', views.contact_page, name='contact'),    
    # Protected pages (require login)
    path('', login_required(views.home), name='feed-home'),
    path('article/<int:pk>/', login_required(views.article_detail), name='article-detail'),
    path('translate/', login_required(views.translate_article), name='translate-article'),
    path('summarize/', login_required(views.summarize_article), name='summarize-article'),
    path('recommendation/', login_required(views.recommendation), name='feed'),
    path('latest/', login_required(views.latest_feed), name='latest-feed'),
    path("analyze-sentiment/", login_required(views.analyze_sentiment), name="analyze-sentiment"),
]