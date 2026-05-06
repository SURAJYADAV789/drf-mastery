from django.urls import path
from .views import RegisterView, LoginView, ProfileView, RefreshTokenView, LogoutView, PostListCreateView,PostDetailView, CommentListCreateView, CommentDetailView

urlpatterns = [
    path('register/', RegisterView.as_view(),name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/',ProfileView.as_view(),name='profile'),
    path('token/refresh/',RefreshTokenView.as_view(),name='token-refresh'),
    path('logout/',LogoutView.as_view(),name='logout'),

    # Posts (resource-based)
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),


    # Comments (nested under posts)
    path('posts/<int:post_pk>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('posts/<int:post_pk>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]