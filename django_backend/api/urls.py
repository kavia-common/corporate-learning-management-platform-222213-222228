from django.urls import path
from .views import health

# PUBLIC_INTERFACE
urlpatterns = [
    path("health/", health, name="Health"),
]
