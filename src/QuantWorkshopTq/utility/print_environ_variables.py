# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


import os
import pprint


def print_environ_variables():
    pprint.pprint(dict(os.environ), width=1)
