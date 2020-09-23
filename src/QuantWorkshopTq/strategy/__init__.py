# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from .base import StrategyBase, StrategyParameter
from .utility import get_logger, get_application_path
from .database import db_session, get_table_order, TQOrder, TQTrade

from .moving_average import double_moving_average
from .popcorn import PopcornStrategy
from .scalping import Scalping
