import logging 
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .models import Entity, Trip, TripDetail, LogDetail,LogBook,ActivityLog
from .serializers import EntitySerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .serializers import UserRegistrationSerializer,TripSerializer, TripDetailSerializer, LogDetailSerializer, LogBookSerializer, ActivityLogSerializer
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
    logger.info(f"get trip detail {serializer.data}")
    return Response(serializer.data)


def parse_location_string(location_str):
    """Convert 'lat,lng' string to a dictionary {latitude: lat, longitude: lng}."""
    try:
        lat, lng = map(float, location_str.split(","))
        return {"latitude": lat, "longitude": lng}
    except ValueError:
        logger.error(f"Invalid location format: {location_str}")
        return None

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_trip_detail(request, trip_id):
    """Create a TripDetail for a trip (user must own the trip)"""
    

    # Fetch trip and check if user owns it
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    

    # Check if a TripDetail already exists for this trip
    if TripDetail.objects.filter(trip=trip).exists():
        logger.warning(f"TripDetail already exists for trip {trip_id}")
        return Response({"error": "TripDetail already exists for this trip"}, status=400)

    # Convert location strings to dictionaries
    data = request.data.copy()
    data["trip"] = trip.id

    for field in ["pickup_location", "dropoff_location", "current_location"]:
        if field in data and isinstance(data[field], str):
            parsed_location = parse_location_string(data[field])
            if parsed_location:
                data[field] = parsed_location
            else:
                return Response({field: "Invalid location format. Expected 'lat,lng'."}, status=400)

    # Validate and create the TripDetail
    serializer = TripDetailSerializer(data=data)
    if serializer.is_valid():
        try:
            trip_detail = serializer.save()
            logger.info(f"TripDetail created successfully: {trip_detail}")
            return Response(serializer.data, status=201)
        except Exception as e:
            logger.error(f"Error saving TripDetail: {e}", exc_info=True)
            return Response({"error": f"Error saving TripDetail: {str(e)}"}, status=500)
    else:
        logger.warning(f"Validation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=400)

@api_view(['PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_or_delete_trip_detail(request, trip_id):
    logger.info(f"UPDATE {trip_id}")
    logger.info(f"UPDATE {trip_id}")
    """ Update or delete TripDetail (only if the user owns the trip) """
    trip = get_object_or_404(Trip, id=trip_id, users=request.user)
    logger.info(f"trip found {trip_id}")
    trip_detail = get_object_or_404(TripDetail, trip=trip)
    logger.info(f"trip_detail found {trip_id}")

    if request.method == 'PUT':
        # Copy request data and set trip ID
        data = request.data.copy()
        data["trip"] = trip.id

        # Parse location strings
        for field in ["pickup_location", "dropoff_location", "current_location"]:
            if field in data and isinstance(data[field], str):
                parsed_location = parse_location_string(data[field])
                if parsed_location:
                    data[field] = parsed_location
                else:
                    return Response({field: "Invalid location format. Expected 'lat,lng'."}, status=400)

        # Validate and update the TripDetail
        logger.info(f"UPDATE DATA {data}")
        serializer = TripDetailSerializer(trip_detail, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        logger.info("aboute to delete")
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
    logger.info(f"Attempting to create LogDetail for trip ID: {trip_id}, User: {request.user}")
    try:
        trip = get_object_or_404(Trip, id=trip_id, users=request.user)
        data = request.data.copy()
        data["trip"] = trip.id  # Ensure trip ID is linked
        
        serializer = LogDetailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
    except Trip.DoesNotExist:
        return Response({"error": "Trip not found or permission denied."}, status=404)
    except Exception as e:
        return Response({"error": "An unexpected error occurred."}, status=500)

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



@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def log_book_view(request, log_detail_id):
    """Handles GET and POST requests for LogBook."""
    if request.method == 'GET':
        log_book = get_object_or_404(LogBook, log_detail_id=log_detail_id)
        serializer = LogBookSerializer(log_book)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        data['log_detail'] = log_detail_id
        serializer = LogBookSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def log_book_detail_view(request, log_detail_id):
    """Handles PUT and DELETE requests for LogBook."""
    log_book = get_object_or_404(LogBook, log_detail_id=log_detail_id)

    if request.method == 'PUT':
        serializer = LogBookSerializer(log_book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        log_book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_activity_log(request, log_book_id):
    logger.info(f"log_book_id (log_detail_id) received: {log_book_id}")
    logger.info(f"Request data: {request.data}")
    """
    Creates a new ActivityLog entry for a given LogBook.
    """
    try:
        log_detail = get_object_or_404(LogDetail, pk=log_book_id)
        log_book = log_detail.log_book
    except LogDetail.DoesNotExist:
        return Response({"error": "LogDetail not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ActivityLogSerializer(data=request.data, context={'log_book': log_book}) #add context

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_activity_log(request, log_book_id, activity_log_id):
    """
    Deletes an ActivityLog entry.
    """
    try:
        activity_log = get_object_or_404(ActivityLog, log_book_id=log_book_id, pk=activity_log_id)
    except ActivityLog.DoesNotExist:
        return Response({"error": "ActivityLog not found."}, status=status.HTTP_404_NOT_FOUND)

    activity_log.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Example to create many ActivityLog at once.
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_many_activity_logs(request, log_book_id):
    """
    Creates multiple ActivityLog entries for a given LogBook.
    """
    try:
        log_book = get_object_or_404(LogBook, pk=log_book_id)
    except LogBook.DoesNotExist:
        return Response({"error": "LogBook not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ActivityLogSerializer(data=request.data, many=True) # many = True important here
    if serializer.is_valid():
        serializer.save(log_book=log_book)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










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

