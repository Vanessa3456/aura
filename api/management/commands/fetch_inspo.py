import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import InspoImage

class Command(BaseCommand):
    help='Fetches random fashion inspiration images from Unsplash'
    def handle(self, *args, **kwargs):
        # the styles aura cares about
        search_terms =[
            'streetwear', 
            'y2k fashion', 
            'minimalist style',
            'vintage outfit',
            'sneakers'
            ]
        
        # Unsplash allows 30 random images per request
        url = "https://api.unsplash.com/photos/random"
        headers= {
            "Accept-Version":"v1",
            "Authorization":f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"
        }
        
        total_saved= 0
        
        for term in search_terms:
            self.stdout.write(f"Fetching images for: {term}...")
            
            params={
                
                "query":term,
                "count":30,
                "orientation":"portrait"            
            }
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data= response.json()
                
                for photo in data:
                    image_link = photo['urls']['regular']
                    
                    # Clean up the search term to use as a tag (e.g., 'streetwear fashion' -> 'streetwear')
                    clean_tag=term.split()[0]
                    
                    # Save it to our database if we don't already have it
                    obj, created = InspoImage.objects.get_or_create(
                        image_url= image_link,
                        defaults={'style_tags': clean_tag}
                    )
                    
                    if created:
                        total_saved += 1
            else:
                self.stderr.write(f"Error fetching {term}:{response.status_code}")
        self.stdout.write(self.style.SUCCESS(f"Succesfully added {total_saved} new inspo images to the database!"))
        