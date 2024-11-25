import unittest
import sqlalchemy as sa
import sqlalchemy.orm as so


class TestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = sa.create_engine("sqlite:///:memory:", echo=True)
        self.session = so.Session(bind=self.engine)
