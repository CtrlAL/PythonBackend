from typing import Any

import asyncio

from flask import Blueprint, jsonify, request

from shared.presentation.schemas import ShortenRequest, ShortenResponse
from shared.services.url_shortener import UrlShortenerService


def create_writer_blueprint(
    service: UrlShortenerService,
    base_url: str,
) -> Blueprint:
    bp = Blueprint("writer", __name__)

    @bp.route("/api/shorten", methods=["POST"])
    def shorten() -> Any:
        payload = ShortenRequest.model_validate(
            request.get_json(silent=True) or {}
        )

        link = asyncio.run(service.shorten(str(payload.url)))

        response = ShortenResponse(
            code=link.short_code,
            short_url=f"{base_url}/{link.short_code}",
        )

        return jsonify(response.model_dump()), 201

    @bp.route("/healthz", methods=["GET"])
    def health() -> Any:
        return "ok", 200

    return bp
