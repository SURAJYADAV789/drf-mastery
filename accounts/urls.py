from django.urls import path
from .views import RegisterView, LoginView, ProfileView, RefreshTokenView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(),name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/',ProfileView.as_view(),name='profile'),
    path('token/refresh/',RefreshTokenView.as_view(),name='token-refresh'),
    path('logout/',LogoutView.as_view(),name='logout',)
]