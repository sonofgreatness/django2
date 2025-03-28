from django.urls import path
from .views import add_entity, get_entity, register_user, login_user

urlpatterns = [
    path('add-entity/', add_entity, name='add_entity'),
    path('get-entity/', get_entity, name='get_entity'),
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
]

