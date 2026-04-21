from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer
from .utils import normalize_email


class AuthHealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'app': 'authentication'})


class RegisterView(APIView):
    def post(self, request):
        data = request.data.copy()
        if 'email' in data:
            data['email'] = normalize_email(data['email'])

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
