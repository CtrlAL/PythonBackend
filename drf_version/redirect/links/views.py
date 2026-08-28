import os
import redis

from django.http import HttpResponseRedirect, Http404
from django.views import View
from links.data_access import get_long_url


_redis_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
)


class RedirectView(View):
    def get(self, request, code):
        cached_url = _redis_client.get(f"short:{code}")
        if cached_url:
            return HttpResponseRedirect(cached_url.decode())

        long_url = get_long_url(code)
        if not long_url:
            raise Http404()

        _redis_client.setex(f"short:{code}", 3600, long_url)
        return HttpResponseRedirect(long_url)
