from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer, PostSerializer, CommentSerializers, PostReadSerializer, PostWriteSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from .backends import CustomTokenObtainPairSerializer
from .models import Post, Comments
from .services import PostService, CommentService


# Create your views here.
class RegisterView(APIView):
    permission_classes = [AllowAny]  # Anyone can register

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully.",
                    'username': user.username,
                    'email': user.email,
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT token
            refresh = CustomTokenObtainPairSerializer.get_token(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response(
                {
                    'message': 'Login Successfully',
                    'access': access_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                },
                status=status.HTTP_200_OK
            )

            # Refresh Token -> HTTPonly cookie
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,  # JS cannot access this
                # secure=True,    # HTTPS only (set False for local dev)
                secure=settings.COOKIE_SECURE,
                samesite='LAX',  # CSRF protection
                max_age=7 * 24 * 60 * 60  # 7 days in seconds
            )

            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user is populated from the token alone
        # Zero DB call for authentications
        print("User:", request.user)
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "message": "This data came from your token, not a DB session lookup."

            }
        )
    

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Read Refresh Token from HTTPOnly Cookies
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            return Response(
                {'access': new_access_token},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {'message': 'Logout Successful.'},
                status=status.HTTP_200_OK
            )

            # Delete cookie from browser
            response.delete_cookie('refresh_token')

            return response
        
        except TokenError:
            return Response(
                {'error': 'Invalid Token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # GET /posts/ → list all posts
    def get(self, request):
        posts = PostService.get_user_posts(request.user)
        serializer = PostReadSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # POST /posts/ → create a post
    def post(self, request):
        # WRITE → use simple serializer
        serializer = PostWriteSerializer(data=request.data)
        if serializer.is_valid():
            #view ask service to create
            post = PostService.create_post(
                user=request.user,
                validated_data=serializer.validated_data
            )
             # Return rich representation after creation
            return Response(PostReadSerializer(post, context={'request':request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]


    # GET /posts/1/ → get single post
    def get(self, request, pk):
        post = PostService.get_post_by_id(pk)

        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        if post.user != request.user:
            return Response(
                {'error': 'Not your posts'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PUT /posts/1/ → full update
    def put(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PostSerializer(Post, data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PATCH /posts/1/ → partial update
    def patch(self, request, pk):
        post = PostService.get_post_by_id(pk)
        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if post.user != request.user:
            return Response(
                {"error": "Not your post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            post = PostService.update_post(
                post, serializer.validated_data
            )
            return Response(PostSerializer(post).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        post = PostService.get_post_by_id(pk)
        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if post.user != request.user:
            return Response(
                {"error": "Not your post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        PostService.delete_post(post)
        return Response(
            {"message": "Post deleted."},
            status=status.HTTP_204_NO_CONTENT
        )


class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, posk_pk):
        comments = Comments.objects.filter(post__pk=posk_pk)
        serializer = CommentSerializers(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request, post_pk):
        # find the post first
        try:
            post = Post.objects.get(pk=post_pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CommentSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            comment = Comments.objects.get(pk=pk)
            if comment.user != user:
                return None, 'forbidden'
            return comment, None
        except Comments.DoesNotExist:
            return None, 'not_found'
        

    def get(self, request, post_pk, pk):
        comment, error = self.get_object(pk, request.user)
        if error == 'not_found':
            return Response(
                {'error': 'Comment Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if error == 'forbidden':
            return Response(
                {'error': 'Not your comment'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CommentSerializers(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, post_pk, pk):
        comment, error = self.get_object(pk, request.user)
        if error == 'not_found':
            return Response(
                {'error': 'Comment Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if error == 'forbidden':
            return Response(
                {'error': 'Not your comment'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CommentSerializers(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, post_pk, pk):
        comment, error = self.get_object(pk, request.user)
        if error == 'not_found':
            return Response(
                {"error": "Comment not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if error == 'forbidden':
            return Response(
                {"error": "Not your comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(
            {"message": "Comment deleted."},
            status=status.HTTP_204_NO_CONTENT
        )

