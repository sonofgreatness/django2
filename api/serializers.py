from rest_framework import serializers
from .models import Entity, Trip, TripDetail, LogDetail
from django.contrib.auth.models import User
from rest_framework import serializers


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'start_date', 'end_date', 'from_place', 'to_place', 'created_at', 'updated_at']# You can exclude fields if necessary

class TripDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripDetail
        fields = '__all__'

class LogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogDetail
        fields = '__all__'

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
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
