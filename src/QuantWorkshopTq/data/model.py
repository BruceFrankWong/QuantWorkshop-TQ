# -*- coding: utf-8 -*-

__author__ = 'Bruce Frank Wong'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, Column, ForeignKey, Integer, String, DateTime

from QuantWorkshopTq.utility import get_application_path


ModelBase = declarative_base()

db_engine = create_engine(f'sqlite:///{get_application_path()}/test.sqlite', echo=True)
# db_engine = create_engine('postgresql://scott:tiger@localhost/')

# create a configured "Session" class
DatabaseSession = sessionmaker(bind=db_engine)

# create a Session
db_session = DatabaseSession()

metadata = MetaData()


class Exchange(ModelBase):
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    abbr = Column(String, nullable=False)

    futures_list = relationship('Futures', back_populates='exchange')
    options_list = relationship('Options', back_populates='exchange')

    def __repr__(self):
        return f'<Exchange(name={self.name}, fullname={self.fullname}, abbr={self.abbr})>'


class Product(ModelBase):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)


class Futures(ModelBase):
    __tablename__ = 'futures'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='futures_list')


class Options(ModelBase):
    __tablename__ = 'options'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)

    exchange = relationship('Exchange', back_populates='options_list')


def create_all_tables():
    ModelBase.metadata.create_all(db_engine)


def init_exchange():
    db_session.add_all([
        Exchange(name='上期所', fullname='上海期货交易所', abbr='SHFE'),
        Exchange(name='大商所', fullname='大连商品交易所', abbr='DCE'),
        Exchange(name='郑商所', fullname='郑州商品交易所', abbr='CZCE'),
        Exchange(name='中金所', fullname='中国金融期货交易所', abbr='CFFEX'),
        Exchange(name='能源所', fullname='上海国际能源交易中心', abbr='INE'),
    ])
    db_session.commit()


def init_options():
    id_shfe = db_session.query(Exchange).filter_by(abbr='SHFE').one().id
    id_dce = db_session.query(Exchange).filter_by(abbr='DCE').one().id
    id_czce = db_session.query(Exchange).filter_by(abbr='CZCE').one().id
    id_cffex = db_session.query(Exchange).filter_by(abbr='CFFEX').one().id
    id_ine = db_session.query(Exchange).filter_by(abbr='INE').one().id

    db_session.add_all([
        Options(name='黄金', symbol='au', exchange_id=id_shfe),
        Options(name='铜', symbol='cu', exchange_id=id_shfe),
        Options(name='铝', symbol='al', exchange_id=id_shfe),
        Options(name='锌', symbol='zn', exchange_id=id_shfe),
        Options(name='天然橡胶', symbol='ru', exchange_id=id_shfe),

        Options(name='豆粕', symbol='m', exchange_id=id_dce),
        Options(name='玉米', symbol='c', exchange_id=id_dce),
        Options(name='铁矿石', symbol='i', exchange_id=id_dce),
        Options(name='液化石油气', symbol='pg', exchange_id=id_dce),
        Options(name='聚乙烯', symbol='l', exchange_id=id_dce),
        Options(name='聚氯乙烯', symbol='v', exchange_id=id_dce),
        Options(name='聚丙烯', symbol='pp', exchange_id=id_dce),

        Options(name='棉花', symbol='cf', exchange_id=id_czce),
        Options(name='白糖', symbol='sr', exchange_id=id_czce),
        Options(name='聚丙烯', symbol='pp', exchange_id=id_czce),
        Options(name='聚丙烯', symbol='pp', exchange_id=id_czce),

    ])
    db_session.commit()
