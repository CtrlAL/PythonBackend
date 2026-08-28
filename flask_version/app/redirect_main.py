from uvicorn.middleware.wsgi import WSGIMiddleware

from app.main import create_app

flask_app = create_app(include_writer=False, include_redirect=True)
app = WSGIMiddleware(flask_app)
