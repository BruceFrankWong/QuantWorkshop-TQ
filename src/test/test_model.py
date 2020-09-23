# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


from QuantWorkshopTq.database import (
    create_all_tables,
    init_exchange,
    init_futures,
    init_options
)


def init_database():
    init_exchange()
    init_futures()
    init_options()


if __name__ == '__main__':
    # print(get_application_path())
    create_all_tables(drop=True)
    init_database()
