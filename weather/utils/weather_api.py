import hashlib

import requests
from django.conf import settings
from rest_framework import status

API_URL = settings.OPENWEATHER_API_URL
API_KEY = settings.OPENWEATHER_API_KEY


def fetch_city_weather(city_name):
    """Fetch city weather from the API and handle errors."""
    try:
        response = requests.get(API_URL.format(city_name) + API_KEY)
        if response.status_code != 200:
            return None, f"API responded with status code {response.status_code}."

        res = response.json()
        if "main" not in res:
            return None, "Invalid city name."

        city_info = {
            'city': city_name,
            'temp': res["main"]["temp"],
        }
        return city_info, None
    except requests.exceptions.RequestException as e:
        return None, f"An error occurred while fetching data: {str(e)}."


def construct_cache_key(city_name):
    """Construct a cache key using the city name."""
    return hashlib.md5(city_name.encode('utf-8')).hexdigest()


def create_error_response(city_name, error_message):
    """Create a standardized error response."""
    error_response = {
        'city': city_name,
        'error': error_message,
    }
    # Set status code based on the error
    status_code = status.HTTP_400_BAD_REQUEST if "Invalid city name" in error_message else status.HTTP_500_INTERNAL_SERVER_ERROR
    return error_response, status_code
