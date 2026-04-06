from flask import Flask, render_template, send_from_directory
from importlib import resources
from os import path
# from loguru import logger
from uuid import uuid4


class WebApp():
    def __init__(self, mqtt_host: str = None, mqtt_port: int = None) -> None:
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        service_path = path.join(
            resources.files("soundcraftui16mqtt_web"), "data"
        )
        path.split(path.abspath(__file__))[0]
        self.app = Flask(
            __name__, root_path=service_path,
            template_folder=path.join(service_path, "templates")
        )
        self.app.config["SECRET_KEY"] = str(uuid4())
        self.app.config["APPLICATION_ROOT"] = service_path
        self.provide_paths()

    def provide_paths(self) -> None:
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/status")
        def status():
            return render_template(
                "status.html",
                data={
                    "mqtt_host": self.mqtt_host,
                    "mqtt_port": self.mqtt_port
                }
            )

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory(
                path.join(self.app.root_path, "static", "favicon"),
                "favicon-96x96.ico", mimetype="image/vnd.microsoft.icon"
            )


def get_webapp(mqtt_host: str = None, mqtt_port: int = None) -> Flask:
    return WebApp(mqtt_host, mqtt_port).app
