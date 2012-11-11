"""
    This is my first Flask app
"""
from __future__ import with_statement
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from werkzeug import check_password_hash, generate_password_hash

# config
DATABASE = '/tmp/hatemail.db'
DEBUG = False
PER_PAGE = 10
SECRET_KEY = "devopsborat" # choose wisely
PASSWORD = "default" # choose wisely

# make app
app = Flask(__name__)
app.config.from_object(__name__)

def get_db():
    # database connection
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db 

@app.teardown_appcontext
def close_database(exception):
    # Closes database at end of request
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()
    # with closing(get_db()) as db:
    #     with app.open_resource('schema.sql') as f:
    #         db.cursor().executescript(f.read())
    #     db.commit()

        db.execute('''insert into mod (
        pw_hash) values (?)''',
        [generate_password_hash(PASSWORD)])
        db.commit()

def query_db(query, args=(), one=False):
    # Query the db
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    # reestablish mod-ness
    g.mod = None
    if 'mod_id' in session:
        g.mod = query_db('select * from mod where mod_id = ?', [session['mod_id']], one=True)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        #increment entry score
        if request.form['del'] == 'true':
            db = get_db()
            db.execute('''DELETE FROM entry
                WHERE entry_id=?''',[request.form['entry_id']])
            db.commit()
            flash('Deleted')
        else:
            db = get_db()
            db.execute('''UPDATE entry
                SET score = score + 1
                WHERE entry_id=?''',[request.form['entry_id']])
            db.commit()
            flash('Upvoted')
    return render_template('mainline.html', entries=query_db('''
        select entry.* from entry
        where entry.approved = 1
        order by entry.pub_date desc limit ?
        ''',
        [PER_PAGE]))

@app.route("/submit", methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        if not request.form['name']:
            error = 'You have to enter a name'
	    flash(error)
        elif not request.form['content']:
            error = 'You have to enter content'
	    flash(error)
        else:
            db = get_db()
            db.execute('''insert into entry (
            title, content, score, approved, pub_date) values (?, ?, 0, 0,?)''',
            [request.form['name'],request.form['content'],int(time.time())])
            db.commit()
            flash('Successfully submitted! Awaiting approval')
            return redirect(url_for('index'))
    return render_template('submit.html')


@app.route("/auth", methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        mod = query_db('select * from mod', one=True)
        if not request.form['password']:
            error = 'You have to enter a password'
	    flash(error)
        elif not check_password_hash(mod[1], request.form['password']):
            error = 'Invalid password'
	    flash(error)
        else:
            flash('Welcome back, mod')
            session['mod_id'] = mod[0]
            return redirect(url_for('modqueue'))
    return render_template('authenticate.html')

# if there's a post request on this route, authenticate
# if successful redirect to mod interface

@app.route("/admin", methods=['GET', 'POST'])
def modqueue():
    if 'mod_id' not in session:
        abort(401)
    if request.method == 'POST':
        # method to approve a post in the mod queue- this should set the post to approved in db
        db = get_db()
        db.execute('''UPDATE entry
            SET approved=1
            WHERE entry_id=?''',[request.form['entry_id']])
        db.commit()
        flash('Approved')
    return render_template('admin.html', entries=query_db('''
            select entry.* from entry
            where entry.approved = 0
            order by entry.pub_date desc limit ?
            ''',
            [PER_PAGE]))

if __name__ == "__main__":
    app.run()
