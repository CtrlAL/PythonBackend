import os, redis
from django.http import HttpResponseRedirect, Http404
from django.views import View
from links.dao import get_long_url
_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))

class RedirectView(View):
    def get(self, request, code):
        cached = _redis.get(f"short:{code}")
        if cached:
            return HttpResponseRedirect(cached.decode())
        url = get_long_url(code)
        if not url:
            raise Http404()
        _redis.setex(f"short:{code}", 3600, url)
        return HttpResponseRedirect(url)
