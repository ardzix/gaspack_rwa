from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Asset

def homepage(request):
    """Homepage view showing featured assets"""
    assets = Asset.objects.filter(is_deleted=False)[:6]  # Show first 6 assets
    context = {
        'assets': assets,
        'title': 'Gaspack RWA - Real World Asset Crowdfunding'
    }
    return render(request, 'assets/homepage.html', context)

class AssetListView(ListView):
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 12
    
    def get_queryset(self):
        return Asset.objects.filter(is_deleted=False)

class AssetDetailView(DetailView):
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'
    
    def get_queryset(self):
        return Asset.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()
        
        # Add additional context data
        context.update({
            'available_slots': asset.total_slots,  # You can modify this based on purchases
            'total_investment': asset.total_value,
            'roi_percentage': 12.5,  # Example ROI
            'related_assets': Asset.objects.filter(is_deleted=False).exclude(id=asset.id)[:3],
        })
        
        return context
