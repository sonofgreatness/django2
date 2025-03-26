from django.urls import path
from .views import add_entity, get_entity

urlpatterns = [
    path('add/', add_entity, name='add_entity'),
    path('get/', get_entity, name='get_entity'),
]

