from rest_framework import serializers

from .models import ApiKey


class ApiKeySerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(required=False, write_only=True, allow_blank=False)
    masked_key = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApiKey
        fields = (
            'id',
            'name',
            'description',
            'is_active',
            'key_prefix',
            'last_used_at',
            'created_at',
            'updated_at',
            'api_key',
            'masked_key',
        )
        read_only_fields = ('id', 'key_prefix', 'last_used_at', 'created_at', 'updated_at')

    def get_masked_key(self, obj):
        return obj.get_masked_key()

    def create(self, validated_data):
        plaintext_key = validated_data.pop('api_key', None)
        api_key = ApiKey(**validated_data)
        if plaintext_key:
            api_key.set_plaintext_key(plaintext_key)
        else:
            plaintext_key = api_key.generate_key()
        api_key.save()
        api_key.plain_text_key = plaintext_key
        return api_key

    def update(self, instance, validated_data):
        plaintext_key = validated_data.pop('api_key', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if plaintext_key:
            instance.set_plaintext_key(plaintext_key)

        instance.save()
        if plaintext_key:
            instance.plain_text_key = plaintext_key
        return instance
