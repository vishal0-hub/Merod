from django.urls import path

from .views import TradingHealthView, TradePreviewView

urlpatterns = [
    path('health/', TradingHealthView.as_view(), name='trading-health'),
    path('preview/', TradePreviewView.as_view(), name='trade-preview'),
]
