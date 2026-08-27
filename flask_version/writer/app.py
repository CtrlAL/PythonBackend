import os
import sys
import redis
from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from models import db, Link

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))

try:
    from common.base62 import encode
except ImportError:
    from base62 import encode

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
BASE_URL = os.environ.get("BASE_URL", "http://localhost")

@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify(error="url required"), 400
    with app.app_context():
        link = Link(long_url=url)
        db.session.add(link)
        db.session.commit()
        code = encode(link.id)
        link.code = code
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify(error="could not assign code"), 500
    r.setex(f"short:{code}", 3600, url)
    return jsonify(code=code, short_url=f"{BASE_URL}/{code}"), 201

@app.route("/healthz", methods=["GET"])
def health():
    return "ok", 200
