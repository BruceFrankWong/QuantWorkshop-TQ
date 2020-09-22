# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

import csv
import os.path
from datetime import date

from . import (db_session, get_application_path)
from . import (
    TQDirection,
    TQOffset,
    Exchange,
    Holiday,
    Futures,
    Options
)


def init_tq():
    db_session.add_all([
        TQDirection(value='BUY', zh='买'),
        TQDirection(value='SELL', zh='卖'),

        TQOffset(value='OPEN', zh='开'),
        TQOffset(value='CLOSE', zh='平'),
        TQOffset(value='CLOSETODAY', zh='平今'),
    ])
    db_session.commit()


def init_exchange():
    csv_path: str = os.path.join(get_application_path(), 'database', 'csv', 'exchange.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            db_session.add(Exchange(name=row['name'], fullname=row['fullname'], symbol=row['symbol']))
    db_session.commit()


def get_exchange_id(exchange: str) -> int:
    return db_session.query(Exchange).filter_by(symbol=exchange).one().id


def init_holiday():
    db_session.add_all([
        Holiday(begin=date(2020, 1, 1), end=date(2020, 1, 1), reason='元旦'),
        Holiday(begin=date(2020, 1, 24), end=date(2020, 1, 30), reason='春节'),
        Holiday(begin=date(2020, 4, 4), end=date(2020, 4, 6), reason='清明节'),
        Holiday(begin=date(2020, 5, 1), end=date(2020, 5, 5), reason='劳动节'),
        Holiday(begin=date(2020, 6, 25), end=date(2020, 6, 27), reason='端午节'),
        Holiday(begin=date(2020, 10, 1), end=date(2020, 10, 8), reason='国庆节、中秋节'),
    ])
    db_session.commit()


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
