from django.core.cache import cache
import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from weather.models import City
from weather.serializers import CityInfoSerializer
from weather.throttles import CityInfoRateThrottle

appid = "4cd7661d1a8e85b6797e2aee8bc3f005"
url = 'https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=' + appid


class CityInfoViewSet(viewsets.ModelViewSet):
    serializer_class = CityInfoSerializer
    queryset = City.objects.all()
    throttle_classes = [AnonRateThrottle, UserRateThrottle, CityInfoRateThrottle]

    def list(self, request, *args, **kwargs):
        cities = City.objects.all()
        all_cities = []

        for city in cities:
            cache_key = f"weather_{city.name}"
            city_info = cache.get(cache_key)

            if not city_info:
                try:
                    # Attempt to fetch data from the API
                    response = requests.get(url.format(city.name))

                    # Check for API errors
                    if response.status_code != 200:
                        return Response(
                            {
                                'error': f"Could not fetch data for city: {city.name}. API responded with status code {response.status_code}."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE
                        )

                    res = response.json()

                    # Check for invalid city
                    if "main" not in res:
                        return Response(
                            {'error': f"Invalid city name: {city.name}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # If successful, store the weather info
                    city_info = {
                        'city': city.name,
                        'temp': res["main"]["temp"],
                    }
                    # Cache the result for 12 hours (43200 seconds)
                    cache.set(cache_key, city_info, timeout=43200)

                except requests.exceptions.RequestException as e:
                    # Handle network or other request-related errors
                    return Response(
                        {'error': f"An error occurred while fetching data: {str(e)}."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

            all_cities.append(city_info)

        # Customizing the response
        return Response(all_cities)
