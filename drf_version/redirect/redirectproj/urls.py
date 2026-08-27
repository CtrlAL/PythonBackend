from django.urls import path
from links.views import RedirectView
urlpatterns = [path("<str:code>", RedirectView.as_view()), path("healthz", lambda r: __import__("django").http.HttpResponse("ok"))]
