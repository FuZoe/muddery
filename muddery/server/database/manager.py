
import threading
import importlib
import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from django.conf import settings
from muddery.server.database.engines import get_engine
from muddery.server.utils.logger import game_server_logger as logger
from muddery.server.utils.utils import classes_in_path


class Manager(object):
    """
    Database manager.
    """
    _instance_lock = threading.Lock()

    class ClassProperty:
        def __init__(self, method):
            self.method = method

        def __get__(self, instance, owner):
            return self.method(owner)

    @classmethod
    def instance(cls, *args, **kwargs):
        """
        Singleton object.
        """
        if not hasattr(Manager, "_instance"):
            with Manager._instance_lock:
                if not hasattr(Manager, "_instance"):
                    Manager._instance = Manager()
        return Manager._instance

    def __init__(self):
        self.engines = {}
        self.sessions = {}

    def connect(self):
        """
        Create db connections.
        """
        for key, cfg in settings.AL_DATABASES.items():
            try:
                engine = get_engine(cfg["ENGINE"], cfg)
                session = sessionmaker(bind=engine)

                self.engines[key] = engine
                self.sessions[key] = session()
            except Exception as e:
                logger.log_trace("Can not connect to db.")
                raise e

    def create_tables(self):
        """
        Create database tables if they are not exist.
        """
        for key, cfg in settings.AL_DATABASES.items():
            try:
                engine = self.engines[key]
                module = importlib.import_module(cfg["MODELS"])
                tables = [cls for cls in vars(module).values() if inspect.isclass(cls)]
                for table in tables:
                    getattr(table, "__table__").create(engine, checkfirst=True)

            except Exception as e:
                logger.log_trace("Can not connect to db.")
                raise e

    def get_session(self, scheme):
        """
        The session of the database connection.
        """
        return self.sessions.get(scheme)
