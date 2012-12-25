"""
    This is my first Flask app
"""
from __future__ import with_statement
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack, escape
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from werkzeug import check_password_hash, generate_password_hash
from math import ceil

# config
DATABASE = '/tmp/hatemail.db'
DEBUG = True
PER_PAGE = 10
SECRET_KEY = "devopsborat" # choose wisely
PASSWORD = "default" # choose wisely

# make app
app = Flask(__name__)
app.config.from_object(__name__)

# pagination, thanks Flask Snippets!
class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

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

@app.route("/", defaults={'page':1}, methods=['GET', 'POST'])
@app.route("/<int:page>", methods=['GET', 'POST'])
def index(page):
    if 'upvotes' not in session:
    session['upvotes']=[]
    if request.method == 'POST':
        #increment entry score
        if request.form['del'] == 'true':
            db = get_db()
            db.execute('''DELETE FROM entry
                WHERE entry_id=?''',[request.form['entry_id']])
            db.commit()
            flash('Deleted')
        else:
            # check cookie. If already voted, reject. If not, upvote and update cookie.
            if request.form['entry_id'] in session['upvotes']:
                flash('Already Upvoted, dude.')
            else:
                db = get_db()
                db.execute('''UPDATE entry
                    SET score = score + 1
                    WHERE entry_id=?''',[request.form['entry_id']])
                db.commit()
                session['upvotes'].append(request.form['entry_id'])
                flash('Upvoted')
    count = query_db('SELECT Count(*) FROM entry WHERE entry.approved = 1')[0][0]
    entries = query_db('''
        select entry.* from entry
        where entry.approved = 1
        order by entry.pub_date desc limit ?,?
        ''',
        [(page-1)*PER_PAGE, PER_PAGE])
    dictrows = [dict(row) for row in entries]
    for r in dictrows:
            r['title'] = str(r['title'])
            r['content'] = str(r['content'])
            if str(r['entry_id']) in session['upvotes']:
                r['locked'] = 'voted'
            else:
                r['locked'] = 'unvoted'
    if not entries and page != 1:
        abort(404)
    pagination = Pagination(page, PER_PAGE, count)
    return render_template('mainline.html',pagination=pagination,entries=dictrows)

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
            hello = escape(str(request.form['name'])).striptags()
            what = escape(str(request.form['content'])).striptags()
            db.execute('''insert into entry (
            title, content, score, approved, pub_date) values (?, ?, 0, 0,?)''',
            [hello,what,int(time.time())])
            db.commit()
            flash('Successfully submitted! Awaiting moderator approval.')
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
    temp=query_db('''
            select entry.* from entry
            where entry.approved = 0
            order by entry.pub_date desc
            ''')
    dictrows = [dict(row) for row in temp]
    for r in dictrows:
            r['title'] = str(r['title'])
            r['content'] = str(r['content'])
    return render_template('admin.html', entries=dictrows)

@app.route("/about")
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run()
