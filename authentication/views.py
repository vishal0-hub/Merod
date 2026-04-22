from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from .serializers_api_keys import ApiKeySerializer
from .models import ApiKey
from .utils import normalize_email

User = get_user_model()


def issue_token_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token


def rotate_token_for_user(user):
    Token.objects.filter(user=user).delete()
    return Token.objects.create(user=user)


class AuthHealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'app': 'authentication'})


class RegisterView(APIView):
    authentication_classes = []

    def post(self, request):
        data = request.data.copy()
        email = data.get('email')
        if email:
            data['email'] = normalize_email(email)

        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = issue_token_for_user(user)
        return Response(
            {
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = issue_token_for_user(user)

        return Response(
            {
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'token': token.key,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_authenticated': user.is_authenticated,
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        token = rotate_token_for_user(user)

        return Response(
            {
                'message': 'Password changed successfully',
                'token': token.key,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email__iexact=serializer.validated_data['email']).first()
        if user is None:
            return Response(
                {'message': 'If the email exists, a reset payload will be generated.'},
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        return Response(
            {
                'message': 'Password reset payload generated',
                'uid': uid,
                'token': token,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'message': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data['token']):
            return Response({'message': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Token.objects.filter(user=user).delete()
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)


class ApiKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        api_keys = ApiKey.objects.filter(user=request.user).order_by('-created_at')
        serializer = ApiKeySerializer(api_keys, many=True)
        return Response(
            {
                'count': api_keys.count(),
                'results': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ApiKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = serializer.save(user=request.user)

        return Response(
            {
                'message': 'API key created successfully',
                'data': ApiKeySerializer(api_key).data,
                'api_key': getattr(api_key, 'plain_text_key', None),
            },
            status=status.HTTP_201_CREATED,
        )


class ApiKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, pk):
        return ApiKey.objects.get(pk=pk, user=user)

    def get(self, request, pk):
        try:
            api_key = self.get_object(request.user, pk)
        except ApiKey.DoesNotExist:
            return Response({'message': 'API key not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'data': ApiKeySerializer(api_key).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        try:
            api_key = self.get_object(request.user, pk)
        except ApiKey.DoesNotExist:
            return Response({'message': 'API key not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApiKeySerializer(api_key, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        api_key = serializer.save()

        return Response(
            {
                'message': 'API key updated successfully',
                'data': ApiKeySerializer(api_key).data,
                'api_key': getattr(api_key, 'plain_text_key', None),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            api_key = self.get_object(request.user, pk)
        except ApiKey.DoesNotExist:
            return Response({'message': 'API key not found.'}, status=status.HTTP_404_NOT_FOUND)

        api_key.delete()
        return Response({'message': 'API key deleted successfully'}, status=status.HTTP_200_OK)
