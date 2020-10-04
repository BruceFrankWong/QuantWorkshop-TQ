# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from sqlalchemy import create_engine, event, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from QuantWorkshopTq.utility import get_application_path


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


ModelBase = declarative_base()

db_engine = create_engine(f'sqlite:///{get_application_path()}/QuantWorkshop.sqlite', echo=False)
db_session = sessionmaker(bind=db_engine)()
db_metadata = MetaData(bind=db_engine)
db_inspect = inspect(db_engine)


from .model import (
    Exchange,
    Holiday,
    Stock,
    Futures,
    Option,
    BacktestRecord,
    BacktestOrder,
    BacktestTrade
)

from .utility import (
    get_table_instance,
    get_table_name,
    is_database_empty,
    is_table_exist,
    is_table_empty,
    create_table,
    create_all_tables,
    drop_all_tables
)

from .initialize import (
    initialize_exchange,
    initialize_futures,
    initialize_option,
    initialize_table
)

print('Checking database:')
for table_name in ModelBase.metadata.tables.keys():
    print(f'Table <{table_name}> ... ', end='')
    if db_engine.dialect.has_table(db_engine, table_name):
        print('existed. ', end='')
    else:
        create_table(table_name)
        print('created, ', end='')

    if is_table_empty(table_name):
        if initialize_table(table_name):
            print('initialized.')
        else:
            print('still empty.')
    else:
        print('OK.')
print('Checking finished.')
