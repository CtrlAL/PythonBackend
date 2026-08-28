from app import main as _main
from app.presentation.redirect_views import RedirectView


service = _main.build_service()

urlpatterns = [
    __import__("django").urls.path(
        "healthz",
        lambda r: __import__("django").http.HttpResponse("ok"),
    ),
    __import__("django").urls.path(
        "<str:code>", RedirectView.as_view(service=service)
    ),
]
