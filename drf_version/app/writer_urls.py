from app import main as _main
from app.presentation.writer_views import ShortenView


service = _main.build_service()

urlpatterns = [
    __import__("django").urls.path(
        "api/shorten", ShortenView.as_view(service=service)
    ),
    __import__("django").urls.path(
        "healthz",
        lambda r: __import__("django").http.HttpResponse("ok"),
    ),
]
