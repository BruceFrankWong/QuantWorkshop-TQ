# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

import csv
import os.path

from . import (db_session, get_application_path)
from . import (Exchange, Futures, Options)


def init_exchange():
    csv_path: str = os.path.join(get_application_path(), 'database', 'csv', 'exchange.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            db_session.add(Exchange(name=row['name'], fullname=row['fullname'], symbol=row['symbol']))
    db_session.commit()


def get_exchange_id(exchange: str) -> int:
    return db_session.query(Exchange).filter_by(symbol=exchange).one().id


def init_options():
    csv_path: str

    csv_path = os.path.join(get_application_path(), 'database', 'csv', 'options.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            print(row['name'], row['symbol'], row['exchange'])
            print(get_exchange_id(row['exchange']))
            db_session.add(Options(name=row['name'],
                                   symbol=row['symbol'],
                                   exchange_id=get_exchange_id(row['exchange'])
                                   )
                           )
    db_session.commit()


def init_futures():
    csv_path: str
    csv_path = os.path.join(get_application_path(), 'database', 'csv', 'futures.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            print(row['name'], row['symbol'], row['exchange'])
            print(get_exchange_id(row['exchange']))
            db_session.add(Futures(name=row['name'],
                                   symbol=row['symbol'],
                                   exchange_id=get_exchange_id(row['exchange']),
                                   contract_url=row['contract_url'],
                                   size=row['size'],
                                   unit=row['unit'],
                                   margin=row['margin'],
                                   fluctuation=row['fluctuation'],
                                   )
                           )
    db_session.commit()
