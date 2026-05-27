from django.contrib import admin
from .models import InspoImage

@admin.register(InspoImage)
class InspoImageAdmin(admin.ModelAdmin):
    # This creates actual columns in the admin panel!
    list_display = ('id', 'style_tags', 'image_url')