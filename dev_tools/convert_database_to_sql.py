from APIv2.modules.ApplicationModel import TableBase
from sqlalchemy.schema import CreateTable

tables = [t.__table__ for t in TableBase.__subclasses__()]

for table in tables:
    print(CreateTable(table)) # type: ignore
