import sqlalchemy.orm as so


class ServiceBase:
    def __init__(self, dbSession: so.Session) -> None:
        self.dbSession = dbSession
