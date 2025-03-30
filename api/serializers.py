from rest_framework import serializers
from .models import Entity, Trip, TripDetail, LogDetail,Location ,LogBook, ActivityLog
from django.contrib.auth.models import User
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'start_date', 'end_date', 'from_place', 'to_place', 'created_at', 'updated_at']# You can exclude fields if necessary

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "latitude", "longitude", "address"]


class TripDetailSerializer(serializers.ModelSerializer):
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    current_location = LocationSerializer()

    class Meta:
        model = TripDetail
        fields = ["id", "trip", "pickup_location", "dropoff_location", "current_location", "created_at", "updated_at"]

    def create(self, validated_data):
        """Convert lat,lng strings into Location objects before saving"""
        logger.info(f"TripDetailSerializer create() called with validated_data: {validated_data}")

        try:
            pickup_data = validated_data.pop("pickup_location")
            dropoff_data = validated_data.pop("dropoff_location")
            current_data = validated_data.pop("current_location", None)

            logger.info(f"Parsed pickup_data: {pickup_data}, dropoff_data: {dropoff_data}, current_data: {current_data}")

            pickup_location = self.parse_location(pickup_data)
            dropoff_location = self.parse_location(dropoff_data)
            current_location = self.parse_location(current_data) if current_data else None

            trip_detail = TripDetail.objects.create(
                pickup_location=pickup_location,
                dropoff_location=dropoff_location,
                current_location=current_location,
                **validated_data
            )

            logger.info(f"TripDetail created successfully: {trip_detail}")

            return trip_detail
        except Exception as e:
            logger.error(f"Error in create() method: {e}", exc_info=True)
            raise serializers.ValidationError(f"Error creating TripDetail: {str(e)}")

    def parse_location(self, location_data):
        """Handle both string and dictionary location inputs"""
        logger.info(f"parse_location called with data: {location_data}")

        if isinstance(location_data, str):
            try:
                lat, lng = map(float, location_data.split(","))
                location, _ = Location.objects.get_or_create(latitude=lat, longitude=lng)
                logger.info(f"Created/Retrieved Location: {location}")
                return location
            except ValueError as ve:
                logger.error(f"ValueError in parse_location: {ve}", exc_info=True)
                raise serializers.ValidationError("Invalid location format. Expected 'lat,lng' string.")
        elif isinstance(location_data, dict):
            location, _ = Location.objects.get_or_create(**location_data)
            logger.info(f"Created/Retrieved Location: {location}")
            return location
        else:
            logger.error(f"Invalid location data type: {type(location_data)}")
            raise serializers.ValidationError("Invalid location data format.")

    def update(self, instance, validated_data):
        logger.info(f"TripDetailSerializer update() called with validated_data: {validated_data} instance.pickup_location {instance.pickup_location}")

        pickup_data = validated_data.pop("pickup_location",None)
        dropoff_data = validated_data.pop("dropoff_location", None)
        current_data = validated_data.pop("current_location", None)

        if pickup_data:
            instance.pickup_location = self.parse_location(pickup_data)
        if dropoff_data:
            instance.dropoff_location = self.parse_location(dropoff_data)
        if current_data:
            instance.current_location = self.parse_location(current_data)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        logger.info(f"TripDetail updated successfully: {instance}")
        return instance


    def delete(self, instance):
        """Delete a TripDetail instance and its associated Location instances."""
        try:
            pickup_location = instance.pickup_location
            dropoff_location = instance.dropoff_location
            current_location = instance.current_location

            instance.delete()  # Delete the TripDetail instance

            # Delete Location instances if they are not referenced by other TripDetails
            if pickup_location and not TripDetail.objects.filter(pickup_location=pickup_location).exists():
                pickup_location.delete()
            if dropoff_location and not TripDetail.objects.filter(dropoff_location=dropoff_location).exists():
                dropoff_location.delete()
            if current_location and not TripDetail.objects.filter(current_location=current_location).exists():
                current_location.delete()

            logger.info(f"TripDetail and associated locations deleted successfully.")
        except TripDetail.DoesNotExist:
            logger.error(f"TripDetail with id {instance.id} does not exist.")
            raise NotFound(detail="TripDetail not found.")
        except Exception as e:
            logger.error(f"Error in delete() method: {e}", exc_info=True)
            raise serializers.ValidationError(f"Error deleting TripDetail: {str(e)}")   


class LogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogDetail
        fields = '__all__'

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = '__all__'



class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['x_datapoint', 'activity', 'remark']

    def create(self, validated_data):
        logger.info(f"ActivityLogSerializer create called with: {validated_data}")
        log_book = self.context.get('log_book')  # Get log_book from context
        logger.info(f"log_book from context: {log_book}")
        if log_book:
            activity_log = ActivityLog.objects.create(log_book=log_book, **validated_data)
            logger.info(f"ActivityLog created: {activity_log}")
            return activity_log
        else:
            logger.error("log_book not provided in context.")
            raise serializers.ValidationError({"detail": "log_book is required."})

    def validate(self, data):
        logger.info(f"ActivityLogSerializer validate called with: {data}")
        validated_data = super().validate(data)
        logger.info(f"ActivityLogSerializer validate returned: {validated_data}")
        return validated_data


class LogBookSerializer(serializers.ModelSerializer):
    activity_logs = ActivityLogSerializer(many=True, read_only=True)

    class Meta:
        model = LogBook
        fields = '__all__'



class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        extra_kwargs = {
            'password': {'write_only': True}  # Password should not be visible when returned
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user
