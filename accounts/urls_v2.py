from django.urls import path
from .views_v2 import PostListCreateViewV2

urlpatterns = [
    path('posts/', PostListCreateViewV2.as_view(), name='v2-post-list'),
]