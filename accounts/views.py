from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
import secrets
from .serializers import RegisterSerializer, ProfileSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Account created successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.delete()
        return Response({'message': 'Account deleted.'}, status=status.HTTP_204_NO_CONTENT)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            # Store token in Redis for 15 minutes
            cache.set(f"pwd_reset:{token}", user.id, timeout=900)
            
            # Use the hostname from the request or a setting
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password?token={token}"
            
            send_mail(
                'Reset your Trimrr password',
                f'Click here to reset your password: {reset_link}',
                'noreply@trimrr.in',
                [email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass  # Don't reveal if email exists for security
            
        return Response({'message': 'If this email exists, a reset link has been sent.'})

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        user_id = cache.get(f"pwd_reset:{token}")
        
        if not user_id:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(id=user_id)
            user.set_password(password)
            user.save()
            cache.delete(f"pwd_reset:{token}")
            return Response({'message': 'Password reset successful.'})
        except User.DoesNotExist:
            return Response({'error': 'User no longer exists.'}, status=status.HTTP_400_BAD_REQUEST)
