from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token =  super().get_token(user)
    
        # Add custom claims - now the token carries extra info
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff

        return token
    
    