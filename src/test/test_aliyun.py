# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'


"""
本模块测试阿里云PostgreSQL RDS。
"""


import os
from datetime import date

from dotenv import find_dotenv, load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, event, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Date, DateTime


# 加载 .env 变量
load_dotenv(find_dotenv())

# RDS 参数
RDS_HOST: str = os.environ.get('ALIYUN_RDS_HOST')
RDS_PORT: str = os.environ.get('ALIYUN_RDS_PORT')
RDS_ACCOUNT: str = os.environ.get('ALIYUN_PG_ACCOUNT')
RDS_PASSWORD: str = os.environ.get('ALIYUN_PG_PASSWORD')

ModelBase = declarative_base()
db_engine = create_engine(f'postgresql+psycopg2://{RDS_ACCOUNT}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/investment')
db_session = sessionmaker(bind=db_engine)()
db_metadata = MetaData(bind=db_engine)
db_inspect = inspect(db_engine)


class Holiday(ModelBase):
    __tablename__ = 'holiday'

    id = Column(Integer, primary_key=True)
    begin = Column(Date, nullable=False)
    end = Column(Date, nullable=False)
    reason = Column(String)

    def __repr__(self):
        return f'<Holiday(name={self.name}, fullname={self.fullname}, abbr={self.symbol})>'


if __name__ == '__main__':
    ModelBase.metadata.create_all(db_engine, checkfirst=True)
    db_session.add_all([
        Holiday(begin=date(2020, 1, 1), end=date(2020, 1, 1), reason='元旦'),
        Holiday(begin=date(2020, 1, 24), end=date(2020, 1, 30), reason='春节'),
        Holiday(begin=date(2020, 4, 4), end=date(2020, 4, 6), reason='清明节'),
        Holiday(begin=date(2020, 5, 1), end=date(2020, 5, 5), reason='劳动节'),
        Holiday(begin=date(2020, 6, 25), end=date(2020, 6, 27), reason='端午节'),
        Holiday(begin=date(2020, 10, 1), end=date(2020, 10, 8), reason='国庆节、中秋节'),
    ])
    db_session.commit()
