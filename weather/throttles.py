from rest_framework.throttling import SimpleRateThrottle

class CityInfoRateThrottle(SimpleRateThrottle):
    scope = 'cityinfo'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            # Use user ID for authenticated users
            return f"throttle_{self.scope}_{request.user.id}"
        else:
            # Use IP address for anonymous users
            return self.get_ident(request)

    def allow_request(self, request, view):
        # Check if the user is a superuser and adjust the rate dynamically
        if request.user.is_authenticated and request.user.is_superuser:
            base_rate = self.get_rate()
            if base_rate:
                number, period = base_rate.split('/')
                # Set the superuser's rate to 2x
                self.rate = f"{int(number) * 2}/{period}"
        else:
            self.rate = self.get_rate()

        # Use the dynamically set rate for throttling
        return super().allow_request(request, view)

    def get_rate(self):
        # This method now only returns the rate defined in the settings
        return super().get_rate()
