from django.shortcuts import render
from  google import  genai
from rest_framework.views import APIView, Response
from rest_framework import status
from PIL import Image
import base64
from django.conf import settings
import io
from api.models import InspoImage, ParlourItem, BookmarkedFit
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': "Username and password required"}, status=400)
    
    # FIXED: Added the 'j' to objects
    if User.objects.filter(username=username).exists():
        return Response({'error': "Username already taken"}, status=400) 
    
    user = User.objects.create_user(username=username, password=password)
    
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key,
        'username': user.username
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    # FIXED: Added quotes around 'username' and 'password'
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username
        })
    else:
        return Response({'error':'Invalid credentials'}, status=401)

class AuraStylistView(APIView):
    
    permission_classes=[IsAuthenticated]
    
    def post(self, request):
        user=request.user
        user_msg= request.data.get('message')
        wardrobe_items=request.data.get('wardrobe', [])
        chat_history = request.data.get('history',[])
        
        if not user_msg:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    
        system_prompt = f"""
        You are Aura, an elite, Gen-Z fashion AI stylist. You are helpful, trendy, and concise.
        The person you are styling is named {user.username}. Address them by their name naturally every now and then to make it personal.
        
        RULES:
        - If the user asks for general fashion advice or trends, answer normally based on current streetwear and minimalist aesthetics.
        - If the user asks you to build an outfit, you MUST ONLY suggest an outfit using the images provided from their closet.
        - Keep responses under 4 sentences so they fit nicely in a mobile chat bubble.
        - Do not use markdown headers (#), keep text formatting simple.
        - CRITICAL: When you recommend specific items from the user's closet, you MUST include their Item IDs at the very end of your response, formatted exactly like this: [FITS: id1, id2]. 
        - Example output: "Pair that graphic tee with your dark denim for a clean streetwear look, {user.username}. [FITS: 17164213, 17164288]"
        """
        
        #1. Initialize the contents array with Aura's personality rules
        gemini_contents = [system_prompt]
        if not wardrobe_items:
            gemini_contents.append("The user's closet ('My Parlour') is currently empty. If they ask for an outfit from their closet, politely tell them to add items first.")
        else:
            gemini_contents.append("Here are the images of the clothes currently in the user's closet ('My Parlour'):")
            
            for item in wardrobe_items:
                item_id= item.get('id', 'Unkown')
                category = item.get('category', 'Unknown')
                base64_str=item.get('image_data')
                
                if base64_str:
                    try:
                        image_bytes = base64.b64decode(base64_str)
                        # FIXED: Changed Bytes10 to BytesIO
                        image = Image.open(io.BytesIO(image_bytes)) 
                        
                        # Give Gemini the image AND tell it what category it is                        
                        gemini_contents.append(f"Item ID: {item_id} |Category: {category}")
                        gemini_contents.append(image)
                    except Exception as e:
                        print(f"Failed to decode image for {category}: {e}")
        if(chat_history):
            gemini_contents.append("\n--- RECENT CONVERSATION HISTORY ---")
            for msg in chat_history:
                # tell the ai who said what
                role="User" if msg.get('isUser') else 'Aura'
                past_text= msg.get('text', '')
                gemini_contents.append(f"{role}:{past_text}")
            gemini_contents.append("-----------------------------------\n")
                    
        gemini_contents.append(f"\nUser:{user_msg}\nAura:")
        
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=gemini_contents
            )
            
            return Response({"reply":response.text},status=status.HTTP_200_OK)
        except Exception as e:
            error_msg = str(e)
            print(f"CRITICAL AI ERROR: {error_msg}")
            
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "429" in error_msg:
                return Response(
                    {"reply": "Whoa, I'm getting way too many styling requests right now! Give me a few minutes to catch my breath and ask me again. In the meantime, you can check your discover page for some nice inspos"},                  
                    status=status.HTTP_200_OK
                )
            return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiscoverFeedView(APIView):
    def get(self, request):
        # The '?' tells Django to shuffle the database and grab 20 random images
        images=InspoImage.objects.all().order_by('?')[:20]
        
        # Package the data into a clean dictionary format for Flutter
        data= [
            {'url': img.image_url, 'tags':img.style_tags}
            for img in images
        ]
        
        return Response(data)
    
# --- 1. CLOUD CLOSET UPLOAD ---
@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Only users with a VIP Token can upload
@parser_classes([MultiPartParser, FormParser])
def upload_clothing(request):
    user = request.user 
    
    print("\n--- INCOMING UPLOAD ---")
    print("Files received:", request.FILES)
    print("Data received:", request.data)
    print("-----------------------\n")
    
    # Grab the physical file and the text category from Flutter
    image_file = request.FILES.get('image')
    category = request.data.get('category')

    if not image_file or not category:
        return Response({'error': 'Image and category are required'}, status=400)

    # Save it to the database! Cloudinary automatically intercepts the image file.
    item = ParlourItem.objects.create(
        user=user,
        category=category,
        image=image_file
    )

    return Response({
        'message': 'Successfully added to Cloud Closet!',
        'id': item.id,
        'image_url': item.image.url, 
        'category': item.category
    }, status=201)


# --- 2. BOOKMARK TOGGLE ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request):
    user = request.user
    
    # Grab the URL and Tag from Flutter
    image_url = request.data.get('image_url')
    style_tag = request.data.get('style_tag')

    if not image_url or not style_tag:
        return Response({'error': 'Image URL and style tag are required'}, status=400)

    # Check if this user already bookmarked this exact image
    existing_bookmark = BookmarkedFit.objects.filter(user=user, image_url=image_url).first()

    if existing_bookmark:
        # If it exists, they tapped it again to un-bookmark it
        existing_bookmark.delete()
        return Response({'message': 'Bookmark removed'}, status=200)
    else:
        # If it doesn't exist, save it
        BookmarkedFit.objects.create(user=user, image_url=image_url, style_tag=style_tag)
        return Response({'message': 'Bookmark saved'}, status=201)
    
# --- 3. FETCH USER WARDROBE ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wardrobe(request):
    items= ParlourItem.objects.filter(user=request.user).order_by('-created_at')
    
    data=[
        {
            'id':item.id,
            'imagePath':item.image.url,
            'category':item.category
        }
        for item in items
    ]
    return Response(data, status=200)

# --- 4. FETCH USER bookmarks ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarks(request):
    bookmarks= BookmarkedFit.objects.filter(user=request.user).order_by('-created_at')
    
    data=[
        {
            'url':b.image_url,
            'tag':b.style_tag
        }
        for b in bookmarks
        
    ]
    return Response(data, status=200)


# --- 5. SEARCH INSPO IMAGES ---
@api_view(['GET'])
@permission_classes([AllowAny])
def search_inspo(request):
    # Grab the search word from the URL (e.g., ?q=vintage)
    query= request.GET.get('q','').lower()
    
    if not query:
        return  Response([])
    
    # 'icontains' tells Django to search for the word inside the tags, ignoring upper/lowercase!
    images= InspoImage.objects.filter(style_tags__icontains=query).order_by('?')[:20]
    
    data=[
        {'url':img.image_url, 'tags':img.style_tags}
        for img in images
    ]
    
    return Response(data, status=200)