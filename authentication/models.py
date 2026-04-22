from django.contrib.auth.models import AbstractUser
from django.db import models

from .utils import encrypt_value, generate_api_key, mask_api_key, safe_decrypt_value


class User(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class ApiKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    key_prefix = models.CharField(max_length=12, editable=False)
    encrypted_key = models.TextField(editable=False)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def set_plaintext_key(self, plaintext_key: str):
        self.key_prefix = plaintext_key[:12]
        self.encrypted_key = encrypt_value(plaintext_key)

    def generate_key(self):
        plaintext_key = generate_api_key()
        self.set_plaintext_key(plaintext_key)
        return plaintext_key

    def get_plaintext_key(self):
        return safe_decrypt_value(self.encrypted_key)

    def get_masked_key(self):
        plaintext_key = self.get_plaintext_key()
        if not plaintext_key:
            return '********'
        return mask_api_key(plaintext_key)
