from django.db import models
from django.contrib.auth.models import User # <-- Make sure you have this
from cloudinary.models import CloudinaryField
# Create your models here.
class InspoImage(models.Model):
    image_url=models.URLField(max_length=500)
    style_tags= models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.style_tags

class ParlourItem(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name='wardrobe')
    category= models.CharField(max_length=50)
    
    # This automatically talks to Cloudinary to handle the heavy image file
    image= CloudinaryField('image')
    created_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.category}"
    
class BookmarkedFit(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    image_url= models.URLField(max_length=500)
    style_tag= models.CharField(max_length=50)
    created_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} saved {self.style_tag}"

