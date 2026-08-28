from uvicorn.middleware.wsgi import WSGIMiddleware

from app.main import create_app

flask_app = create_app(include_writer=True, include_redirect=False)
app = WSGIMiddleware(flask_app)
