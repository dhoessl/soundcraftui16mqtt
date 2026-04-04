from sqlite3 import connect, OperationalError
from importlib import resources
from os import path, mkdir
from loguru import logger


class DBConnection:
    def __init__(self, path: str = "/opt/mididatabase/config.db") -> None:
        self.location = path
        self._create_location()
        self.connection = None
        self.connect()
        self._setup_database()

    def _create_location(self) -> None:
        if not path.exists(path.split(self.location)[0]):
            mkdir(path.split(self.location)[0])
            logger.warning(f"{path.split(self.location)[0]} created")

    def connect(self) -> None:
        if self.is_alive():
            self.connection.close()
            self.connection = None
        try:
            self.connection = connect(self.location)
        except OperationalError as error:
            raise RuntimeError(f"Error while connecting to DB\n{error}")

    def is_alive(self) -> bool:
        try:
            self.connection.cursor()
            return True
        except Exception:
            return False

    def execute(
        self, query: str | int, params: tuple | dict = None,
        commit: bool = False
    ) -> list:
        if not self.is_alive():
            self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                query if type(query) is str else self.queries[query],
                params if params else ()
            )
            if commit:
                self.connection.commit()
        except OperationalError as error:
            raise RuntimeError(
                f"Database execute error while execute query\n{error}"
            )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def _setup_database(self) -> None:

        try:
            # with open("/opt/mididatabase/init.sql", "r") as fp:
            with open(
                resources.files("soundcraftui16_database.data")
                .joinpath("init.sql"),
                "r"
            ) as fp:
                data = fp.read()
        except FileNotFoundError:
            logger.critical("Init File not found - Abort Program")
            raise RuntimeError("Database Init file missing")
        commands = data.split("\n\n")
        for command in commands:
            self.execute(command, commit=True)
        # Setup master mix entry
        misc_entries = [
            {
                "parameter": "master",
                "value": 0
            },
            {
                "parameter": "bpm",
                "value": 60
            }
        ]
        for default in misc_entries:
            self.execute(
                "INSERT INTO misc (parameter, value) "
                "SELECT :parameter, :value "
                "WHERE NOT EXISTS"
                "(SELECT 1 FROM misc WHERE parameter = :parameter)",
                {"parameter": default["parameter"], "value": default["value"]},
                True
            )
        # Setup Channels entries
        for channel in range(12):
            self.execute(
                "INSERT INTO channel (id) "
                "SELECT :channel "
                "WHERE NOT EXISTS (SELECT 1 FROM channel WHERE id = :channel)",
                {"channel": channel}, True
            )
            # Setup channels specific fx send entries
            for fx in range(4):
                self.execute(
                    "INSERT INTO channel_fx (channel_id, fx_id) "
                    "SELECT :channel_id, :fx_id "
                    "WHERE NOT EXISTS "
                    "(SELECT 1 FROM channel_fx WHERE channel_id = :channel_id "
                    "AND fx_id = :fx_id)",
                    {"channel_id": channel, "fx_id": fx},
                    True
                )
        # Setup fx settings entries
        for fx in range(4):
            self.execute(
                "INSERT INTO fx (id) SELECT :fx "
                "WHERE NOT EXISTS (SELECT 1 FROM fx WHERE id = :fx)",
                {"fx": fx}, True
            )
