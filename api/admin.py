from django.contrib import admin
from .models import Trip, TripDetail, LogDetail, Location, LogBook, ActivityLog

admin.site.register(Trip)
admin.site.register(TripDetail)
admin.site.register(LogDetail)
admin.site.register(Location)
admin.site.register(LogBook)
admin.site.register(ActivityLog)

