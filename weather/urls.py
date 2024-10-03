from rest_framework import routers

from weather.views import CityInfoViewSet

router = routers.SimpleRouter()
router.register(r'', CityInfoViewSet, basename='cities')
urlpatterns = router.urls