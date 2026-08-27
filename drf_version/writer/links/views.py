import os, redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from links.serializers import URLSerializer
from links.dao import insert_link, get_long_url
from snowflake import Snowflake
from base62 import encode

_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
_sf = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_BASE = os.environ.get("BASE_URL", "http://localhost")

class ShortenView(APIView):
    def post(self, request):
        ser = URLSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        long_url = ser.validated_data["url"]
        code = encode(_sf.next_id())
        insert_link(code, long_url)
        _redis.setex(f"short:{code}", 3600, long_url)
        return Response({"code": code, "short_url": f"{_BASE}/{code}"}, status=status.HTTP_201_CREATED)

def get_long_url_cached(code):
    return get_long_url(code)
