import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """
        Serialize into JSON formatted object
        :return: JSON formatted object
        """

        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, backref=backref("items",
                                                      cascade="all, "
                                                              "delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref=backref("items",
                                              cascade="all, "
                                                      "delete-orphan"))

    @property
    def serialize(self):
        """
        Serialize into JSON formatted object
        :return: JSON formatted object
        """

        return {
            'name': self.name,
            'id': self.id,
            'created_at': self.created_at
        }


engine = create_engine('postgresql:///catalog')
Base.metadata.create_all(engine)
