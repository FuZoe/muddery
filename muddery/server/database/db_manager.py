
import threading
import importlib
import inspect
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from muddery.server.settings import SETTINGS
from muddery.server.database.engines import get_engine, get_db_link
from muddery.server.utils.logger import logger
from muddery.server.utils.singleton import Singleton


class DBManager(Singleton):
    """
    Database manager.
    """
    def __init__(self):
        self.engines = {}
        self.sessions = {}
        self.connected = False

    def connect(self):
        """
        Create db connections.
        """
        if self.connected:
            return

        for key, cfg in SETTINGS.DATABASES.items():
            try:
                engine = get_engine(cfg["ENGINE"], cfg)
                self.engines[key] = engine
                self.sessions[key] = Session(engine, autocommit=True)
            except Exception as e:
                logger.log_trace("Can not connect to db.")
                raise e

        self.connected = True

    def create_tables(self):
        """
        Create database tables if they are not exist.
        """
        for key, cfg in SETTINGS.DATABASES.items():
            try:
                engine = self.engines[key]
                module = importlib.import_module(cfg["MODELS"])
                tables = [cls for cls in vars(module).values() if inspect.isclass(cls) and hasattr(cls, "__table__")]
                for table in tables:
                    getattr(table, "__table__").create(engine, checkfirst=True)

            except Exception as e:
                logger.log_trace("Can not connect to db.")
                raise e

    def get_db_link(self, scheme):
        """
        The session of the database connection.
        """
        db_link = ""
        if scheme in SETTINGS.DATABASES:
            cfg = SETTINGS.DATABASES[scheme]
            db_link = get_db_link(cfg["ENGINE"], cfg)

        return db_link

    def get_engine(self, scheme):
        """
        The session of the database connection.
        """
        return self.engines.get(scheme)

    def get_session(self, scheme):
        """
        The session of the database connection.
        """
        return self.sessions.get(scheme)

    def get_tables(self, scheme):
        """
        Get all tables' names of a scheme.
        """
        if scheme not in SETTINGS.DATABASES:
            logger.log_trace("Scheme %s dose not exits." % scheme)
            raise KeyError

        module = importlib.import_module(SETTINGS.DATABASES[scheme]["MODELS"])
        tables = [cls.__tablename__ for cls in vars(module).values()
                  if inspect.isclass(cls) and hasattr(cls, "__tablename__")]
        return tables

    def clear_table(self, scheme, table_name):
        """
        clear all data in a table.
        """
        # get model
        session = self.sessions.get(scheme)
        if not session:
            return

        config = SETTINGS.DATABASES[scheme]
        module = importlib.import_module(config["MODELS"])
        model = getattr(module, table_name)
        stmt = delete(model)
        session.execute(stmt)

    def get_model(self, scheme, table_name):
        """
        Get the table's ORM model.
        """
        if scheme in SETTINGS.DATABASES:
            config = SETTINGS.DATABASES[scheme]
            module = importlib.import_module(config["MODELS"])
            model = getattr(module, table_name)
            return model
