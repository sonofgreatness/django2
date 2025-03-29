import logging 
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .models import Entity, Trip, TripDetail, LogDetail
from .serializers import EntitySerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .serializers import UserRegistrationSerializer,TripSerializer, TripDetailSerializer, LogDetailSerializer
from rest_framework.authtoken.models import Token
from  rest_framework.authentication import TokenAuthentication 


logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 5  # Items per page
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_user_trips(request):
    """ List all trips for the authenticated user with pagination """
    trips = Trip.objects.filter(users=request.user)
    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(trips, request)
    serializer = TripSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_trip(request):
    """ Create a new trip and link it to the authenticated user """
    
    logger.info(f"create_trip called with request.data: {request.data}")  # Debugging log

    # Create a new Trip instance without expecting users from request data
    serializer = TripSerializer(data=request.data)
    
    if serializer.is_valid():
        trip = serializer.save()  # Save the trip instance
        trip.users.add(request.user)  # Associate with logged-in user
        logger.info(f"Trip created successfully: {serializer.data}")
        return Response(serializer.data, status=201)
    
    logger.error(f"Trip creation failed: {serializer.errors}")  # Log errors
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trip_details(request, trip_id):
    """ Retrieve a specific trip's details (only for the authenticated user) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    trip_detail = TripDetail.objects.filter(trip=trip).first()
    log_detail = LogDetail.objects.filter(trip=trip).first()

    trip_serializer = TripSerializer(trip)
    trip_detail_serializer = TripDetailSerializer(trip_detail) if trip_detail else None
    log_detail_serializer = LogDetailSerializer(log_detail) if log_detail else None

    return Response({
        "trip": trip_serializer.data,
        "trip_detail": trip_detail_serializer.data if trip_detail else None,
        "log_detail": log_detail_serializer.data if log_detail else None
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trip(request, trip_id):
    """
    Retrieve a specific trip that belongs to the authenticated user.
    """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    serializer = TripSerializer(trip)
    return Response(serializer.data, status=200)
    


@api_view(['PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_or_delete_trip(request, trip_id):
    """ Update or delete a trip (only by the owner) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)

    if request.method == 'PUT':
        serializer = TripSerializer(trip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        trip.delete()
        return Response({"message": "Trip deleted successfully"}, status=204)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_recent_trip(request):
    """ Get the most recent trip with related LogDetail and TripDetail """
    trip = Trip.objects.filter(users=request.user).order_by('-start_date').first()
    if not trip:
        return Response({"error": "No trips found"}, status=404)

    trip_detail = TripDetail.objects.filter(trip=trip).first()
    log_detail = LogDetail.objects.filter(trip=trip).first()

    trip_serializer = TripSerializer(trip)
    trip_detail_serializer = TripDetailSerializer(trip_detail) if trip_detail else None
    log_detail_serializer = LogDetailSerializer(log_detail) if log_detail else None

    return Response({
        "trip": trip_serializer.data,
        "trip_detail": trip_detail_serializer.data if trip_detail else None,
        "log_detail": log_detail_serializer.data if log_detail else None
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_log_details_for_trip(request, trip_id):
    """ List all LogDetails for a given trip (only for the authenticated user) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    log_details = LogDetail.objects.filter(trip=trip)
    
    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(log_details, request)
    serializer = LogDetailSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)   


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trip_detail(request, trip_id):
    """ Retrieve trip details for a specific trip (user must own the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    trip_detail = TripDetail.objects.filter(trip=trip).first()
    
    if not trip_detail:
        return Response({"error": "Trip detail not found"}, status=404)

    serializer = TripDetailSerializer(trip_detail)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_trip_detail(request, trip_id):
    """ Create TripDetail for a trip (user must own the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    
    # Ensure there's only one TripDetail per Trip
    if TripDetail.objects.filter(trip=trip).exists():
        return Response({"error": "TripDetail already exists for this trip"}, status=400)

    data = request.data.copy()
    data["trip"] = trip.id  # Ensure trip ID is linked

    serializer = TripDetailSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

@api_view(['PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_or_delete_trip_detail(request, trip_id):
    """ Update or delete TripDetail (only if the user owns the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    trip_detail = get_object_or_404(TripDetail, trip=trip)

    if request.method == 'PUT':
        serializer = TripDetailSerializer(trip_detail, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        trip_detail.delete()
        return Response({"message": "TripDetail deleted successfully"})


### -------------------- LOG DETAIL CRUD -------------------- ###

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_log_detail(request, trip_id):
    """ Retrieve LogDetail for a specific trip (user must own the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    log_detail = LogDetail.objects.filter(trip=trip).first()
    
    if not log_detail:
        return Response({"error": "Log detail not found"}, status=404)

    serializer = LogDetailSerializer(log_detail)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_log_detail(request, trip_id):
    """ Create LogDetail for a trip (user must own the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    
    # Ensure there's only one LogDetail per Trip
    if LogDetail.objects.filter(trip=trip).exists():
        return Response({"error": "LogDetail already exists for this trip"}, status=400)

    data = request.data.copy()
    data["trip"] = trip.id  # Ensure trip ID is linked

    serializer = LogDetailSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

@api_view(['PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_or_delete_log_detail(request, trip_id):
    """ Update or delete LogDetail (only if the user owns the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    log_detail = get_object_or_404(LogDetail, trip=trip)

    if request.method == 'PUT':
        serializer = LogDetailSerializer(log_detail, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        log_detail.delete()
        return Response({"message": "LogDetail deleted successfully"}, status=204)



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
    logger.info("Received login request...") 

    username = request.data.get("username")
    password = request.data.get("password")

    logger.debug(f"Username received: {username}")  
    logger.debug(f"Password received: {'***' if password else 'No password provided'}")

    if not username or not password:
        logger.error("Error: Missing username or password")  
        return Response({"error": "Missing username or password"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is None:
        logger.warning("Authentication failed: Invalid credentials")  
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    logger.info(f"Authentication successful for user: {user.username}")  
    login(request, user)
    logger.info("User logged in successfully")
    token, created = Token.objects.get_or_create(user=user)
    logger.info(f"Token {'created' if created else 'retrieved'}: {token.key}")
    return Response({"message": "Login successful", "token": token.key}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    request.session.flush()
    return Response({"message": "Logged out"}, status=status.HTTP_200_OK)

