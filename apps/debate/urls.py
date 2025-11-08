from django.urls import path
from . import views

urlpatterns = [
       path('', views.debate_page, name='debate_page'),
        path('<int:article_id>/', views.debate_page, name='debate_article'),  # /debate/7/
        path('stream/', views.stream_debate, name='stream_debate'),
]
