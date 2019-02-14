from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
from . import config

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(48), nullable=False)
    email = Column(String(64), nullable=False, unique=True)
    password = Column(String(128), nullable=False)

    def __repr__(self):
        return "<User (id={},name={},email={},password={})>".format(self.id, self.name, self.email, self.password)


class Post(Base):
    __tablename__ = 'post'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    postdate = Column(DateTime, nullable=False)

    author = relationship('User')
    content = relationship('Content', uselist=False)

    def __repr__(self):
        return "<User (id={},title={},author_id={})>".format(self.id, self.title, self.author_id)


class Content(Base):
    __tablename__ = 'content'

    id = Column(BigInteger, ForeignKey('post.id'), primary_key=True)
    content = Column(LONGTEXT, nullable=False)

    def __repr__(self):
        return "<User (id={},content={})>".format(self.id, self.content[:20])


# 连接数据库
engine = create_engine(config.URL, echo=config.DATABASE_DEBUG)


# 创建删除表
def createtables():
    Base.metadata.create_all(engine)


def droptables():
    Base.metadata.drop_all(engine)

# createtables()

Session = sessionmaker(bind=engine)
session = Session()
