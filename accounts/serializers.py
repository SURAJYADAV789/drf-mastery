from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Post, Comments

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type':'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type':'password'}
    )

    class Meta:
        model = User
        fields = ['username','email','password','password2']

    
    # validate both passwords
    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    # Validate email is unique
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value
    
    # Create User
    def create(self, validated_data):
        validated_data.pop('password2')   # remove password2 not needed
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")

        attrs['user'] = user
        return attrs


class PostSerializer(serializers.ModelSerializer):
    # show username instead of user id
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CommentSerializers(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comments
        fields = ['id', 'user', 'post', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'post', 'created_at']

        

class UserRepresentationSerializer(serializers.ModelSerializer):
    """
    How a user looks when nested inside another resource
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PostRepresentationSerializer(serializers.ModelSerializer):
    user = UserRepresentationSerializer(read_only=True)

    # Custom field — computed, not in DB
    word_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'title', 'content',
            'word_count', 'is_owner',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_word_count(self, obj):
        return len(obj.content.split())
    
    def get_is_owner(self, obj):
        # Access request via content
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user

        return False



class PostWriteSerializer(serializers.ModelSerializer):
    """
    What the client sends to CREATE or UPDATE a post
    Simple. Just the fields we need.
    """
    class Meta:
        model = Post
        fields = ['title', 'content']


class PostReadSerializer(serializers.ModelSerializer):
    """
    What the client receives when READING a post
    Rich. Full nested data.
    """
    user = UserRepresentationSerializer(read_only=True)
    word_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'title', 'content',
            'word_count', 'is_owner',
            'created_at', 'updated_at'
        ]

    def get_word_count(self, obj):
        return len(obj.content.split())

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False