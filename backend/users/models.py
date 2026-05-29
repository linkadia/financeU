import uuid

from django.db import models

class UserProfile(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    username = models.CharField(max_length=80, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    operator_token = models.CharField(max_length=255, blank=True, editable=False)
    password_hash = models.CharField(max_length=128, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    onboarding_interests = models.JSONField(default=list, blank=True)
    onboarding_risk_profile = models.CharField(max_length=40, blank=True)
    onboarding_goal = models.CharField(max_length=60, blank=True)
    selected_agent = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or self.email
