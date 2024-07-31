from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask_app import flask_app as flask_app
from dash_app import app as dashboard

application = DispatcherMiddleware(
    flask_app,
    {
        "/dashboard": dashboard.server,
    },
)

if __name__ == "__main__":
    run_simple(
        "localhost",
        8050,
        application,
        threaded=True,
        use_debugger=True,
        reloader_type="stat",
    )
