from flask import Flask, render_template, send_from_directory
from importlib import resources
from os import path
# from loguru import logger
from uuid import uuid4


class WebApp():
    def __init__(self, name, root_path) -> None:
        service_path = path.join(
            resources.files("soundcraftui16mqtt_web"), "data"
        )
        path.split(path.abspath(__file__))[0]
        self.app = Flask(name, root_path)
        self.app.config["SECRET_KEY"] = str(uuid4())
        self.app.config["APPLICATION_ROOT"] = service_path
        self.provide_paths()

    def provide_paths(self) -> None:
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory(
                path.join(self.app.root_path, "static", "favicon"),
                "favicon-96x96.ico", mimetype="image/vnd.microsoft.icon"
            )
