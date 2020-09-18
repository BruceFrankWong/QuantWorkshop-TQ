# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

import os.path


def get_application_path() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
