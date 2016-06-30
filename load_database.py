from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, Base

engine = create_engine('postgresql:///catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Catalogs
category1 = Category(id=1, name="Soccer")
category2 = Category(id=2, name="Basketball")
category3 = Category(id=3, name="Baseball")
category4 = Category(id=4, name="Frisbee")
category5 = Category(id=5, name="Snowboarding")
category6 = Category(id=6, name="Rock Climbing")
category7 = Category(id=7, name="Football")
category8 = Category(id=8, name="Skating")
category9 = Category(id=9, name="Hockey")


session.add(category1)
session.add(category2)
session.add(category3)
session.add(category4)
session.add(category5)
session.add(category6)
session.add(category7)
session.add(category8)
session.add(category9)
session.commit()

print "loaded!"
