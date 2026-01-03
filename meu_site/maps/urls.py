from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path('', views.mapa_plotly, name='home'),
    path('violence_3m/', views.mapa_plotly, {'filename': 'pred_3_anyviolence__off_period.csv'}, name='mapa_violence_3m'),
    path('violence_12m/', views.mapa_plotly, {'filename': 'pred_12_anyviolence__off_period.csv'}, name='mapa_violence_12m'),
    path('conflict_3m/', views.mapa_plotly, {'filename': 'pred_3__off_period.csv'}, name='mapa_conflict_3m'),
    path('conflict_12m/', views.mapa_plotly, {'filename': 'pred_12__off_period.csv'}, name='mapa_conflict_12m'),
    path('report/', views.report, name='report'),
    path('resposta/', views.resposta, name='resposta'),
    path('baixar_pdf/', views.baixar_pdf, name='baixar_pdf'),
    path('model/', views.model, name='model'),
    path('about/', views.about, name='about'),
    path('upload/', views.upload_csv, name='upload'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]