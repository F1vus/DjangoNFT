from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    eth_account_address = models.CharField(max_length=42, blank=True)

    def __str__(self):
        return self.eth_account_address
