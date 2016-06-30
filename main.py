import string

from flask import Flask, render_template
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
import random

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine("postgresql:///catalog")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route("/")
@app.route("/catalog/")
def showCataglog():
    """
    Show the main page
    """
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by("created_at").limit(10)
    return render_template("catalog.html", categories=categories,
                           latest_items=latest_items)


@app.route('/catalog/<int:category_id>/items')
def showCategoryItems(category_id):
    """"
    Show the selected category's items
    """
    return render_template("categoryitems.html")


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


if __name__ == "__main__":
    ## app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
