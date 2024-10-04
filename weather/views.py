from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from icecream import ic
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from weather.models import City
from weather.serializers import CityInfoSerializer
from weather.throttles import CityInfoRateThrottle
from weather.utils.weather_api import fetch_city_weather, construct_cache_key, create_error_response

CACHE_TIMEOUT = 10  # 5 minutes in seconds

def get_city_weather_info(city_name):
    cache_key = construct_cache_key(city_name)
    city_info = cache.get(cache_key)

    if not city_info:
        city_info, error_message = fetch_city_weather(city_name)
        if error_message:
            return None, cache_key, create_error_response(city_name, error_message)

        # Cache the result for future requests
        cache.set(cache_key, city_info, timeout=CACHE_TIMEOUT)

    return city_info, cache_key, None

class CityInfoViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CityInfoSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle, CityInfoRateThrottle]
    http_method_names = ['get', 'post', 'delete']

    @extend_schema(
        description="Retrieve weather information for all cities with caching.",
        responses={
            200: OpenApiResponse(
                response=CityInfoSerializer(many=True),
                description="Weather information retrieved successfully."
            ),
            404: OpenApiResponse(description="City not found.")
        }
    )
    def list(self, request, *args, **kwargs):
        cities = City.objects.all()
        all_cities = []
        min_ttl = CACHE_TIMEOUT  # Initialize with the maximum possible TTL

        for city in cities:
            city_info, cache_key, error_response = get_city_weather_info(city.name)
            if error_response:
                return Response(*error_response)

            all_cities.append(city_info)

            # Get the TTL for each city and find the minimum
            ttl = cache.ttl(cache_key) if cache_key in cache else CACHE_TIMEOUT
            if ttl < min_ttl:
                min_ttl = ttl

        response = Response(all_cities)
        response['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
        response['Expires'] = CACHE_TIMEOUT
        ic(min_ttl)
        response['Expires-In'] = min_ttl  # Set the minimum TTL
        return response

    @extend_schema(
        description="Retrieve weather information for a specific city.",
        responses={
            200: OpenApiResponse(
                response=CityInfoSerializer,
                description="Weather information retrieved successfully."
            ),
            404: OpenApiResponse(description="City not found.")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        city = self.get_object()
        city_info, cache_key, error_response = get_city_weather_info(city.name)
        if error_response:
            return Response(*error_response)

        response = Response(city_info)
        response['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
        response['Expires'] = CACHE_TIMEOUT
        ic(cache.ttl(cache_key))
        expires_in = cache.ttl(cache_key) if cache_key in cache else CACHE_TIMEOUT
        response['Expires-In'] = expires_in  # Set the TTL for the specific city
        return response
