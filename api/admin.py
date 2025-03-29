from django.contrib import admin
from .models import Trip, TripDetail, LogDetail, Location

admin.site.register(Trip)
admin.site.register(TripDetail)
admin.site.register(LogDetail)
admin.site.register(Location)
