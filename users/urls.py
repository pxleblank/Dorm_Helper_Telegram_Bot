from django.urls import path
from . import views

urlpatterns = [
    path('unverified_users/', views.unverified_users, name='unverified_users'),
    path('verify_user/<int:user_id>/', views.verify_user),
    path('delete_user/<int:user_id>/', views.delete_user),
]
