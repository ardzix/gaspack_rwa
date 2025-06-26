from django.db import models
from django.conf import settings
from assets.models import Asset
import uuid

class SimulatedNFT(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    token_id = models.CharField(max_length=100, unique=True)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage of total slots
    slots_owned = models.PositiveIntegerField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'asset']
    
    def __str__(self):
        return f"NFT {self.token_id} - {self.user.username} owns {self.ownership_percentage}% of {self.asset.name}"
    
    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = f"GASPACK_{self.asset.id}_{self.user.id}"
        if not self.ownership_percentage:
            self.ownership_percentage = (self.slots_owned / self.asset.total_slots) * 100
        super().save(*args, **kwargs)
