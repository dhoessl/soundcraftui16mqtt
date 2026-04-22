from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Event, Lock
from importlib import resources
from loguru import logger
from time import sleep


class TestServer:
    def __init__(
        self, ip: str = "127.0.0.1", port: int = 80,
        max_connection: int = 32
    ) -> None:
        """Demo for soundcraft ui16 for debuging"""
        self.ip = ip
        self.port = port
        self.max_connection = max_connection
        self.terminate_server = Event()
        self.clients = []
        self.clients_lock = Lock()
        self.controll_thread = None

    def run(self) -> None:
        self.controll_thread = Thread(
            target=self._controll_thread,
            args=()
        )
        self.controll_thread.start()

    def _controll_thread(self) -> None:
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            sock.bind((self.ip, self.port))
            sock.listen(self.max_connection)
            logger.info("Test Server started")
            while not self.terminate_server.is_set():
                conn, addr = sock.accept()
                thread = Thread(
                    target=self._server_thread,
                    args=(conn, addr)
                )
                self.clients.append(thread)
                thread.start()
                logger.info("New client accepted")
            for client in self.clients:
                client.join()

    def start(self) -> None:
        self.run()

    def terminate(self) -> None:
        self.terminate_server.set()
        self.controll_thread.join()

    def stop(self) -> None:
        self.terminate()

    def _server_thread(self, conn, addr) -> None:
        buffer = ""
        with conn:
            self.dump_config(conn)
            while not self.terminate_server.is_set():
                buffer += conn.recv(1024).decode()
                if "\n" not in buffer:
                    continue
                parts = buffer.split("\n")
                data = parts[0:len(parts)-1]
                buffer = parts[len(parts)-1]
                for message in data:
                    if message.startswith("SETD^"):
                        self.send_config_change(f"{message}\n")
                if "GET /raw HTTP1.1" in data:
                    self.dump_config(conn)
                if "GET /vu_test HTTP1.1" in data:
                    self.dump_vu2(conn)
                if "ALIVE" in data:
                    conn.sendall("OK\n".encode())

    def dump_vu2(self, conn) -> None:
        logger.info("Trying to send vutest data")
        with open(
            resources.files("soundcraftui16mqtt_mixer.data")
            .joinpath("test_vu2.txt"),
            "r"
        ) as fp:
            data = fp.read()
        for line in data.split("\n"):
            conn.sendall(f"{line}\n".encode())
            sleep(0.08)

    def dump_config(self, conn) -> None:
        with open(
            resources.files("soundcraftui16mqtt_mixer.data")
            .joinpath("test_startup.txt"),
            "r"
        ) as fp:
            data = fp.read()
        for line in data.split():
            config_message = f"{line}\n"
            conn.sendall(config_message.encode())

    def send_config_change(self, message: str) -> None:
        dead_clients = []
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.sendall(message.encode())
                except (ConnectionResetError, BrokenPipeError, OSError):
                    dead_clients.append(client)
            for client in dead_clients:
                self.clients.remove(client)
