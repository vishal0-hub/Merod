from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TradeRequestSerializer
from .utils import normalize_symbol


class TradingHealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'app': 'trading'})


class TradePreviewView(APIView):
    def post(self, request):
        data = request.data.copy()
        if 'symbol' in data:
            data['symbol'] = normalize_symbol(data['symbol'])

        serializer = TradeRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                'message': 'Trade payload validated',
                'data': serializer.validated_data,
            },
            status=status.HTTP_200_OK,
        )
