from django.urls import path, include

urlpatterns = [
    path('home/', include('mapa.urls')),
]