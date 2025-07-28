from django.urls import path
from . import views

urlpatterns = [
    path('', views.mapa_plotly, name='home'),
    path('about/', views.about_view, name='about'),
    path('model/', views.model_view, name='model'),  # ✅ nova URL
    path('<str:filename>/', views.mapa_plotly, name='mapa_plotly'),
]
