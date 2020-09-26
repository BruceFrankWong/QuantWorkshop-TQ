# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, event, MetaData, inspect
from sqlalchemy.orm import sessionmaker

from QuantWorkshopTq.utility import get_application_path


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')


ModelBase = declarative_base()

db_engine = create_engine(f'sqlite:///{get_application_path()}/test.sqlite', echo=True)
db_session = sessionmaker(bind=db_engine)()
db_metadata = MetaData(bind=db_engine)
db_inspect = inspect(db_engine)

event.listen(db_engine, 'connect', _fk_pragma_on_connect)


from .model import (
    Exchange,
    Holiday,
    Stock,
    Futures,
    Option
)

from .utility import (
    get_table_instance,
    get_table_name,
    is_database_empty,
    is_table_exist,
    is_table_empty,
    create_all_tables,
    drop_all_tables
)

from .initialize import (
    init_exchange,
    init_futures,
    init_option,
)
