from django.urls import path
from .views import AuraStylistView, DiscoverFeedView,register_user, login_user, upload_clothing, toggle_bookmark,get_wardrobe, get_bookmarks,search_inspo
urlpatterns = [
    path('chat/', AuraStylistView.as_view(), name='aura-chat'),
    path('discover/', DiscoverFeedView.as_view(), name='discover-feed'),
    
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    
    # Upload & Toggle (Sending data to Django)    
    path('wardrobe/upload/', upload_clothing, name='upload-clothing'),
    path('bookmarks/toggle/', toggle_bookmark, name='toggle-bookmark'),
    
    # Fetching data from Django 
    path('wardrobe/', get_wardrobe, name='get-wardrobe'),
    path('bookmarks/', get_bookmarks, name='get-bookmarks'),
    
    path('discover/search/', search_inspo, name='search_inspo'),

]