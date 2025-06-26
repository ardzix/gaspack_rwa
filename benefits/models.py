from django.db import models
from django.conf import settings
from assets.models import Asset
import uuid

class BenefitRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    min_nft_required = models.PositiveIntegerField(help_text="Minimum number of NFT slots required to claim this benefit")
    benefit_type = models.CharField(max_length=50, choices=[
        ('cashback', 'Cashback'),
        ('discount', 'Discount'),
        ('access', 'Exclusive Access'),
        ('dividend', 'Dividend'),
        ('other', 'Other'),
    ])
    benefit_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Value of the benefit")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.asset.name}"
    
    class Meta:
        ordering = ['min_nft_required']

class UserBenefitClaim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    benefit_rule = models.ForeignKey(BenefitRule, on_delete=models.CASCADE)
    claim_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ], default='pending')
    claimed_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.benefit_rule.name}"
    
    class Meta:
        unique_together = ['user', 'benefit_rule']
