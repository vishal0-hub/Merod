from django.contrib.auth import login as django_login
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from rest_framework import status
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
from .utils import get_session_key, get_session_store, get_user_id_from_session, normalize_email

User = get_user_model()


class AuthHealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'app': 'authentication'})


class RegisterView(APIView):
    def post(self, request):
        data = request.data.copy()
        email = data.get('email')
        if email:
            data['email'] = normalize_email(email)

        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        django_login(request, user)

        return Response(
            {
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'session_key': request.session.session_key,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    authentication_classes = []

    def post(self, request):
        session_key = get_session_key(request)

        if not session_key:
            return Response(
                {'message': 'Session key is required. Send the session_key from login or keep cookies enabled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        get_session_store(session_key).delete()
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
    authentication_classes = []

    def post(self, request):
        session_key = get_session_key(request)

        if not session_key:
            return Response(
                {'message': 'Session key is required. Send the session_key from login or keep cookies enabled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = get_user_id_from_session(session_key)

        if not user_id:
            return Response({'message': 'No active session found.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'message': 'No active session found.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request, 'user': user})
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        django_request = request._request
        django_request.user = user
        update_session_auth_hash(django_request, user)

        return Response(
            {
                'message': 'Password changed successfully',
                'session_key': session_key,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
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
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
