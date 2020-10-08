# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


import os.path
import pprint

from dotenv import find_dotenv, load_dotenv
from tqsdk import TqAuth

from .app_path import get_application_path


def get_tq_auth() -> TqAuth:
    print(get_application_path())
    if 'TQ_ACCOUNT' not in os.environ or 'TQ_PASSWORD' not in os.environ:
        load_dotenv(find_dotenv())
    tq_account: str = os.environ['TQ_ACCOUNT']
    tq_password: str = os.environ['TQ_PASSWORD']

    del os.environ['TQ_ACCOUNT']
    del os.environ['TQ_PASSWORD']
    pprint.pprint(dict(os.environ), width=1)

    return TqAuth(tq_account, tq_password)
