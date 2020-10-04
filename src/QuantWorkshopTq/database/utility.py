# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from typing import Union
import csv
import os.path

from QuantWorkshopTq.utility import get_application_path
from . import (ModelBase, db_engine, db_session, db_metadata, db_inspect)


def get_table_instance(table_name: str) -> ModelBase:
    return db_metadata.tables.get(table_name)


def get_table_name(table_instance: ModelBase) -> str:
    return table_instance.__tablename__


def is_database_empty() -> bool:
    table_name_list: list = db_inspect.get_table_names()
    return table_name_list == []


def is_table_exist(table: Union[ModelBase, str]) -> bool:
    table_name: str
    if isinstance(table, str):
        table_name = table
    else:
        table_name = get_table_name(table)
    return table_name in db_metadata.tables.keys()


def is_table_empty(table: Union[ModelBase, str]) -> bool:
    table_instance: ModelBase
    if isinstance(table, str):
        table_instance = ModelBase.metadata.tables.get(table)
    else:
        table_instance = table
    return False if db_session.query(table_instance).first() else True
    # table_name: str
    # if isinstance(table, str):
    #     table_name = table
    # else:
    #     table_name = get_table_name(table)
    # return False if db_session.query(table_name).first() else True


def create_table(table: str, drop: bool = False):
    table_instance: ModelBase = ModelBase.metadata.tables[table]
    table_instance.create(db_engine, checkfirst=True)


def create_all_tables(drop: bool = False):
    if drop:
        drop_all_tables()
    ModelBase.metadata.create_all(db_engine)


def drop_all_tables():
    ModelBase.metadata.drop_all(db_engine)
    db_metadata.reflect(db_engine)
