from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Event
from time import sleep
from loguru import logger


class MixerBase:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.connection_timeout = 5
        self.connect_retry = 30
        self.client = None
        self.exit = Event()
        self.alive_thread = Thread(
            target=self._keep_alive_thread,
            args=()
        )
        self.alive_timeout = 5
        self.recv_thread = Thread(
            target=self._recv_thread,
            args=()
        )
        self.connected = False

    def _keep_alive_thread(self) -> None:
        """ Keeps the connection to soundcraft ui16 alive """
        while not self.exit.is_set():
            self._send_alive()
            sleep(self.alive_timeout)
        logger.warning("Keep alive Thread ended")

    def _send_alive(self) -> None:
        """ Sends alive Message to Mixer to keep connection open """
        try:
            self.client.send(b"ALIVE\n")
        except socket.timeout:
            logger.error("Timeout while sending alive")
            self.connected = False
        except ConnectionResetError:
            logger.critical("Connection was reset by mixer")
            self.exit.set()

    def _recv_thread(self) -> None:
        """ Basic Thread to sink messages. This is required to keep connection
        alive """
        while not self.exit.is_set():
            _ = self.client.recv(512).decode()

    def connect(self) -> bool:
        if self.exit.is_set():
            self.exit.clear()
        self.client = socket(AF_INET, SOCK_STREAM)
        self.client.settimeout(self.connection_timeout)
        connect_count = 0
        logger.debug(f"Trying to connect to mixer at {self.ip}:{self.port}")
        while not self.connected:
            try:
                self.client.connect((self.ip, self.port))
                self.client.send(b"GET /raw HTTP1.1\n\n")
                self._send_alive()
                self.connected = True
            except OSError as oserr:
                if oserr.errno == 101:
                    raise RuntimeError(f"Network of {self.ip} not reachable")
                elif oserr.errno == 103:
                    logger.warning(f"Connection to {self.ip} aborted")
                elif oserr.errno == 113:
                    logger.warning(f"Unable to connect to {self.ip}")
                else:
                    logger.error(
                        f"Unexpected OSError {oserr.errno} while connection "
                        "to mixer"
                    )
                    raise RuntimeError(f"Unexpected OSError: {oserr.errno}")
                connect_count += 1
                logger.debug(f"Connection Retry: {connect_count}")
                sleep(1)
                if connect_count > self.connect_retry:
                    raise RuntimeError(
                        f"Could not connect within {connect_count} tries"
                    )
            except Exception as ex:
                raise RuntimeError(f"Unexpected Error: {ex}")
        logger.debug("Connection to mixer established. Starting keepalive.")
        self.alive_thread.start()
        self.recv_thread.start()

    def terminate(self) -> None:
        self.exit.set()
        if self.alive_thread.is_alive():
            self.alive_thread.join()
        if self.recv_thread.is_alive():
            self.recv_thread.join()
        try:
            self.client.close()
        except Exception as ex:
            logger.error(f"Abnormal termination. Exception {ex}")
            return None
        logger.debug("Disconnected from Soundcraft UI16")
        self.connected = False
