import logging 
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Entity
from .serializers import EntitySerializer
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer
from rest_framework.authtoken.models import Token
from  rest_framework.authentication import TokenAuthentication 


logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_entity(request):
    logger.info("post callwd")
    serializer = EntitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_entity(request):
    logger.info("get_entity called")
    entity = Entity.objects.first()
    if entity:
        serializer = EntitySerializer(entity)
        return Response(serializer.data)
    return Response({"message": "No data found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def register_user(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    user.save()

    return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_user(request):
    logger.info("Received login request...")  # ✅ Step 1: Log function call

    username = request.data.get("username")
    password = request.data.get("password")

    logger.debug(f"Username received: {username}")  # ✅ Step 2: Log input (debug level)
    logger.debug(f"Password received: {'***' if password else 'No password provided'}")

    if not username or not password:
        logger.error("Error: Missing username or password")  # ✅ Log error
        return Response({"error": "Missing username or password"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is None:
        logger.warning("Authentication failed: Invalid credentials")  # ✅ Log authentication failure
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    logger.info(f"Authentication successful for user: {user.username}")  # ✅ Log authentication success
    login(request, user)
    logger.info("User logged in successfully")
    token, created = Token.objects.get_or_create(user=user)
    logger.info(f"Token {'created' if created else 'retrieved'}: {token.key}")
    return Response({"message": "Login successful", "token": token.key}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    request.session.flush()  # Clears the session
    return Response({"message": "Logged out"}, status=status.HTTP_200_OK)

