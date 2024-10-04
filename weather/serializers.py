from rest_framework import serializers

from weather.models import City


class CityInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['name']
