# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

import csv
import os.path
from datetime import date

from sqlalchemy.orm.exc import NoResultFound

from . import (db_session, get_application_path)
from . import (
    Exchange,
    Holiday,
    Futures,
    Option
)


def initialize_exchange():
    csv_path: str = os.path.join(get_application_path(), 'database', 'csv', 'exchange.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            db_session.add(Exchange(name=row['name'], fullname=row['fullname'], symbol=row['symbol']))
    db_session.commit()


def get_exchange_id(exchange: str) -> int:
    return db_session.query(Exchange).filter_by(symbol=exchange).one().id


def initialize_holiday():
    try:
        exchange_list = db_session.query(Exchange).all()
        csv_path: str = os.path.join(get_application_path(), 'database', 'csv', 'holiday.csv')
        with open(csv_path, newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                for exchange in exchange_list:
                    db_session.add(
                        Holiday(begin=date.fromisoformat(row['begin']),
                                end=date.fromisoformat(row['end']),
                                reason=row['reason'],
                                exchange_id=exchange.id
                                )
                    )
        db_session.commit()
    except NoResultFound:
        print('no')
        exit(-1)
    # db_session.add_all([
    #     Holiday(begin=date(2020, 1, 1), end=date(2020, 1, 1), reason='元旦'),
    #     Holiday(begin=date(2020, 1, 24), end=date(2020, 1, 30), reason='春节'),
    #     Holiday(begin=date(2020, 4, 4), end=date(2020, 4, 6), reason='清明节'),
    #     Holiday(begin=date(2020, 5, 1), end=date(2020, 5, 5), reason='劳动节'),
    #     Holiday(begin=date(2020, 6, 25), end=date(2020, 6, 27), reason='端午节'),
    #     Holiday(begin=date(2020, 10, 1), end=date(2020, 10, 8), reason='国庆节、中秋节'),
    # ])
    # db_session.commit()


def initialize_option():
    csv_path: str

    csv_path = os.path.join(get_application_path(), 'database', 'csv', 'options.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            db_session.add(Option(name=row['name'],
                                  symbol=row['symbol'],
                                  exchange_id=get_exchange_id(row['exchange'])
                                  )
                           )
    db_session.commit()


def initialize_futures():
    csv_path: str
    csv_path = os.path.join(get_application_path(), 'database', 'csv', 'futures.csv')
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
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


initializer_list: dict = {
    'exchange': initialize_exchange,
    'holiday': initialize_holiday,
    'option': initialize_option,
    'futures': initialize_futures,
}


def initialize_table(table_name: str) -> bool:
    if table_name in initializer_list.keys():
        initializer_list[table_name]()
        return True
    else:
        return False
