import json
import random
import string
import httplib2
import requests
from flask import Flask, render_template, request, make_response, flash, \
    redirect, url_for, jsonify
from flask import session as login_session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, Person

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine("postgresql:///catalog")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# API Endpoint for Item
@app.route("/catalog/item/<int:item_id>/JSON")
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item.serialize)


@app.route('/login')
def showLogin():
    """
    Show the loging page
    """
    if 'username' in login_session:
        return redirect(url_for('showCatalog'))

    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/login/google', methods=['POST'])
def gconnect():
    """
    Connect to Google Plus
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/logout')
def logout():
    """
    Log out of current session
    """
    if "gplus_id" in login_session:
        return redirect(url_for('gdisconnect'))
    else:
        return redirect(url_for('showCatalog'))


@app.route('/logout/google')
def gdisconnect():
    """
    Log user out of google plus session
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('showCataglog'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(current_login_session):
    """
    Create New User
    :param current_login_session:
    :return: new user's id
    """
    new_user = Person(name=current_login_session['username'],
                      email=current_login_session[
                          'email'], picture=current_login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(Person).filter_by(
        email=current_login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(Person).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(Person).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route("/")
@app.route("/catalog/")
def showCatalog():
    """
    Show the main page
    """
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by("created_at").limit(10)

    current_logged_in_user_id = getUserID(login_session.get('email'))
    return render_template("catalog.html", categories=categories,
                           latest_items=latest_items,
                           current_logged_in_user_id=current_logged_in_user_id)


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def newItem():
    """
    Handles the creation of new item
    """
    if 'username' not in login_session:
        return redirect('/login')
    current_logged_in_user_id = getUserID(login_session.get('email'))
    if request.method == 'POST':
        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        category_id=request.form[
                            'category_id'], user_id=current_logged_in_user_id)
        session.add(new_item)
        flash('New Item %s Successfully Created' % new_item.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template('newitem.html', categories=categories,
                               current_logged_in_user_id=current_logged_in_user_id)


@app.route("/catalog/item/<int:item_id>/edit", methods=['GET', 'POST'])
def editItem(item_id):
    """
    Handles the editing of an item
    """
    if 'username' not in login_session:
        return redirect('/login')

    current_logged_in_user_id = getUserID(login_session.get('email'))
    edit_item = session.query(Item).filter_by(id=item_id).first()

    if edit_item.user_id != current_logged_in_user_id:
        flash('You are not authorised to perform this action!')
        return redirect('/')

    if request.method == 'POST':
        edit_item.name = request.form['name']
        edit_item.description = request.form['description']
        edit_item.category_id = request.form['category_id']
        session.add(edit_item)
        session.commit()
        flash('Item %s Successfully Edited' % edit_item.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template('edititem.html', categories=categories,
                               current_logged_in_user_id=current_logged_in_user_id,
                               item=edit_item)


@app.route("/catalog/item/<int:item_id>/delete")
def deleteItem(item_id):
    """
    Handles the deletion of an item
    """
    if 'username' not in login_session:
        return redirect('/login')

    current_logged_in_user_id = getUserID(login_session.get('email'))
    delete_item = session.query(Item).filter_by(id=item_id).first()

    if delete_item.user_id != current_logged_in_user_id:
        flash('You are not authorised to perform this action!')
        return redirect('/')

    session.delete(delete_item)
    session.commit()
    flash('Item %s Successfully Deleted' % delete_item.name)
    return redirect('/')


@app.route('/catalog/<int:category_id>/items')
def showCategoryItems(category_id):
    """"
    Show the selected category's items
    """
    categories = session.query(Category).all()
    category_items = session.query(Item).filter_by(
        category_id=category_id).order_by(
        "name").all()
    category = session.query(Category).filter_by(id=category_id).first()
    current_logged_in_user_id = getUserID(login_session.get('email'))
    return render_template("categoryitems.html",
                           categories=categories, category=category,
                           category_items=category_items,
                           current_logged_in_user_id=current_logged_in_user_id)


@app.route("/catalog/item/<int:item_id>")
def showItem(item_id):
    """
    Show the item page
    """
    item = session.query(Item).filter_by(id=item_id).first()
    current_logged_in_user_id = getUserID(login_session.get('email'))

    return render_template("item.html", item=item,
                           current_logged_in_user_id=current_logged_in_user_id)


if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
