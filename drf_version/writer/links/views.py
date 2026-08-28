import os, redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from links.serializers import URLSerializer
from links.data_access import insert_link, get_long_url
from snowflake import Snowflake
from base62 import encode

_redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
_id_generator = Snowflake(node_id=int(os.environ.get("NODE_ID", "1")))
_base_url = os.environ.get("BASE_URL", "http://localhost")

class ShortenView(APIView):
    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        long_url = serializer.validated_data["url"]
        code = encode(_id_generator.next_id())
        insert_link(code, long_url)
        _redis_client.setex(f"short:{code}", 3600, long_url)
        return Response({"code": code, "short_url": f"{_base_url}/{code}"}, status=status.HTTP_201_CREATED)

def fetch_long_url_from_db(code):
    return get_long_url(code)
