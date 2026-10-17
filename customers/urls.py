from django.urls import path

from .views import RegistrationView, LoginView, ProfileView, csrf_cookie

urlpatterns = [
    path('csrf/', csrf_cookie, name='csrf-cookie'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
