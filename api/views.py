from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Entity
from .serializers import EntitySerializer

@api_view(['POST'])
def add_entity(request):
    serializer = EntitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_entity(request):
    entity = Entity.objects.first()
    if entity:
        serializer = EntitySerializer(entity)
        return Response(serializer.data)
    return Response({"message": "No data found"}, status=status.HTTP_404_NOT_FOUND)

