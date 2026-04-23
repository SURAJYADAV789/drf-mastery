from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer, PostSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from .backends import CustomTokenObtainPairSerializer
from .models import Post


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
        posts = Post.objects.filter(user=request.user)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # POST /posts/ → create a post
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user) # attached login user 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Post.objects.get(pk=pk, user=user)
        except Post.DoesNotExist:
            return None
        

    # GET /posts/1/ → get single post
    def get(self, request, pk):
        post = self.get_object(pk, request.user)

        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
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
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response(
                {
                    'error': 'Post not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        post.delete()
        return Response(
            {"message": "Post deleted."},
            status=status.HTTP_204_NO_CONTENT
        )

