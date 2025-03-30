from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator


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
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="log_details")  # Use ForeignKey for many-to-one
    start_date = models.DateField()
    total_miles_driven = models.PositiveIntegerField()
    name_of_carrier = models.CharField(max_length=255)
    main_office_address = models.CharField(max_length=255)
    name_of_codriver = models.CharField(max_length=255, blank=True, null=True)
    shipping_document_number = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"LogDetail for {self.trip} on {self.start_date}"





class LogBook(models.Model):
    log_detail = models.OneToOneField(LogDetail, on_delete=models.CASCADE, related_name="log_book")
    date = models.DateField(unique=True)  # One log book per day
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Log Book for {self.date}"

class ActivityLog(models.Model):
    log_book = models.ForeignKey('LogBook', on_delete=models.CASCADE, related_name="activity_logs")
    x_datapoint = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(96)],
        help_text="Represents 15-minute intervals in a 24-hour period (1-96)."
    )
    activity = models.CharField(
        max_length=20,
        choices=[
            ('OFFDUTY', 'Off Duty'),
            ('DRIVING', 'Driving'),
            ('ONDUTY', 'On Duty'),
            ('SLEEPERBERTH', 'Sleeper Berth'),
        ]
    )
    remark = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['x_datapoint'] #Ensures that the activity logs are ordered by x datapoint.

    def __str__(self):
        return f"{self.activity} at x-datapoint {self.x_datapoint} for {self.log_book}"

    @property
    def time_equivalent(self):
        """Returns the time equivalent of the x-datapoint."""
        minutes = (self.x_datapoint - 1) * 15
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours:02d}:{remaining_minutes:02d}"

    @classmethod
    def get_time_from_x_datapoint(cls, x_datapoint):
        """Converts an x-datapoint to a time string."""
        if not 1 <= x_datapoint <= 96:
            raise ValueError("x-datapoint must be between 1 and 96.")
        minutes = (x_datapoint - 1) * 15
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours:02d}:{remaining_minutes:02d}"


