import os

from flask import Flask, redirect, url_for
from . import wom


def create_app():
    app = Flask(__name__)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(wom.bp)

    @app.route("/")
    def index():
        return redirect(url_for("wom.home"))

    return app
