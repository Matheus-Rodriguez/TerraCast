from django.urls import path
from . import views

urlpatterns = [
    path('', views.mapa_plotly, name='home'),  

    path('violence-3m/', views.mapa_plotly, {'filename': 'pred_3_anyviolence__off_period.csv'}, name='mapa_violence_3m'),
    path('violence-12m/', views.mapa_plotly, {'filename': 'pred_12_anyviolence__off_period.csv'}, name='mapa_violence_12m'),
    path('conflict-3m/', views.mapa_plotly, {'filename': 'pred_3__off_period.csv'}, name='mapa_conflict_3m'),
    path('conflict-12m/', views.mapa_plotly, {'filename': 'pred_12__off_period.csv'}, name='mapa_conflict_12m'),

    path('about/', views.about_view, name='about'),
    path('model/', views.model_view, name='model'),
    path('report/', views.report_view, name='report'),
    path('resposta/', views.resposta_view, name='resposta'),
    path('baixar-pdf/', views.baixar_pdf, name='baixar_pdf'),
]
