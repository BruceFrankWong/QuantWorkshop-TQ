# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

import os.path
import logging
from datetime import datetime


def get_logger(strategy_name: str) -> logging.Logger:
    logger = logging.getLogger(f'Strategy')

    logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
    #                               datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(message)s')

    # 当前日期时间
    now: datetime = datetime.now()
    dt: str = now.strftime('%Y-%m-%d_%H-%M-%S')

    # 使用FileHandler输出到文件
    log_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    logger_file = logging.FileHandler(f'{log_path}/Strategy_{strategy_name}_{dt}.txt')
    logger_file.setLevel(logging.DEBUG)
    logger_file.setFormatter(formatter)

    # 使用StreamHandler输出到屏幕
    logger_screen = logging.StreamHandler()
    logger_screen.setLevel(logging.DEBUG)
    logger_screen.setFormatter(formatter)

    # 添加两个Handler
    logger.addHandler(logger_screen)
    logger.addHandler(logger_file)

    return logger


def get_application_path() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
