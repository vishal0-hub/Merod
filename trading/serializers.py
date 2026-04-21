from rest_framework import serializers


class TradeRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=('buy', 'sell'))
    quantity = serializers.DecimalField(max_digits=18, decimal_places=8)
    price = serializers.DecimalField(max_digits=18, decimal_places=8, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
