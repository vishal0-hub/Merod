from django.urls import path

from .views import AuthHealthView, RegisterView

urlpatterns = [
    path('health/', AuthHealthView.as_view(), name='auth-health'),
    path('register/', RegisterView.as_view(), name='register'),
]
