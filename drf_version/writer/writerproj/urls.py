from django.urls import path
from links.views import ShortenView
urlpatterns = [path("api/shorten", ShortenView.as_view()), path("healthz", lambda r: __import__("django").http.HttpResponse("ok"))]
