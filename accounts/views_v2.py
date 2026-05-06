from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . models import Post
from .serializers  import PostSerializer
from rest_framework.permissions import IsAuthenticated

class PostListCreateViewV2(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        post = Post.objects.filter(user=request.user)
        serializer = PostSerializer(post, many=True)

        return Response({
            'count': post.count(),
            'version': 'v2',
            'results': serializer.data
        })
