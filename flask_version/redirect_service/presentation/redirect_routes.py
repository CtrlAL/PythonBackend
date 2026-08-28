from typing import Any

import asyncio

from flask import Blueprint, abort, redirect

from shared.services.url_shortener import LinkNotFoundError, UrlShortenerService


def create_redirect_blueprint(service: UrlShortenerService) -> Blueprint:
    bp = Blueprint("redirect", __name__)

    @bp.route("/<code>", methods=["GET"])
    def redir(code: str) -> Any:
        try:
            url = asyncio.run(service.resolve(code))

        except LinkNotFoundError:
            abort(404)

        return redirect(url, code=302)

    @bp.route("/healthz", methods=["GET"])
    def health() -> Any:
        return "ok", 200

    return bp
