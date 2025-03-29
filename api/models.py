from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# Create your models here.
class Entity(models.Model):
    name = models.CharField(max_length=255)
    message = models.TextField()


class Trip(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    from_place = models.CharField(max_length=255)
    to_place = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=now, editable=False)  # ✅ Added default
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name="trips")  # At least 1 user per trip

    def __str__(self):
        return f"Trip from {self.from_place} to {self.to_place} ({self.start_date} - {self.end_date})"

class Location(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255, blank=True, null=True)  # Optional address
    created_at = models.DateTimeField(default=now, editable=False)  # ✅ Added default
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.address if self.address else f"Lat: {self.latitude}, Lon: {self.longitude}"

class TripDetail(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="trip_detail")  # Exactly 1 trip per TripDetail
    dropoff_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name="dropoffs")
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name="pickups")
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name="current_locations")
    created_at = models.DateTimeField(default=now, editable=False)  # ✅ Added default
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"TripDetail for {self.trip}"

class LogDetail(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="log_detail")  # Each log detail is linked to one trip
    start_date = models.DateField()
    total_miles_driven = models.PositiveIntegerField()
    name_of_carrier = models.CharField(max_length=255)
    main_office_address = models.CharField(max_length=255)
    name_of_codriver = models.CharField(max_length=255, blank=True, null=True)
    shipping_document_number = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=now, editable=False)  # ✅ Added default
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"LogDetail for {self.trip}"



