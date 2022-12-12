from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g

import sqlite3, os, math, time, re

# конфигурация БД

DATABASE = '/tmp/flsite.db'

DEBUG = True

SECRET_KEY = 'aboba228'

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE = os.path.join(app.root_path, 'flsite.db')))

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def getMenu(self):
        sql = '''SELECT * FROM mainmenu'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: 
                return res
        except:
            print('Ошибка чтения из БД')
        return []

    def addPost(self, title, text, url):
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM posts WHERE url LIKE '{url}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print('Статья уже существует')
                return False
            base = url_for('static', filename='images_html')
            text = re.sub(r"(?P<tag><img\s+[^>]*src=)(?P<quote>[\"'])(?P<url>.+?)(?P=quote)>",
                "\\g<tag>" + base + "/\\g<url>>",
                text)

            tm = math.floor(time.time())
            self.__cur.execute('INSERT INTO posts VALUES(NULL, ?, ?, ?, ?)', (title, text, url, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print('Ошибка добавления статьи в БД: ' + str(e))
            return False
        return True
    
    def getPost(self, alias):
        try:
            self.__cur.execute(f"SELECT title, text FROM posts WHERE url LIKE '{alias}' LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print('Ошибка добавления статьи в БД: ' + str(e))
        return(False, False)

    def getPostAnonce(self):
        try:
            self.__cur.execute(f'SELECT id, title, text, url FROM posts ORDER BY time DESC')
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print('Ошибка обращения к БД: ' + str(e))
        return[]

menu = [{'name':'Установка', 'url': 'install-flask'},
        {'name':'Первое приложение', 'url': 'first-app'},
        {'name':'Обратная связь', 'url': 'contact'}]

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db

@app.route('/')
def index():
    db = get_db()
    dbase = FDataBase(db)
    posts = dbase.getPostAnonce()
    return render_template('index.html', title = 'Главная страница', menu = dbase.getMenu(), posts = dbase.getPostAnonce())

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route('/about')
def about():
    db = get_db()
    dbase = FDataBase(db)
    return render_template('about.html', title = 'О сайте', menu = dbase.getMenu())

@app.route('/profile/<username>')
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)
    return f'Пользователь: {username}'

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    db = get_db()
    dbase = FDataBase(db)
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')
    return render_template('contact.html', title = 'Обратная связь', menu = dbase.getMenu())


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'userLogged' in session:
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['username'] == 'selfedu' and request.form['psw'] == '123':
        session['userLogged'] = request.form['username']
        return redirect(url_for('profile', username=session['userLogged']))
    return render_template('login.html', title='Авторизация', menu=menu)

@app.route('/add_post', methods=['POST', 'GET'])
def addPost():
    db = get_db()
    dbase = FDataBase(db)

    if request.method == 'POST':
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category = 'error')
            else:
                flash('Статья успешно добавлена', category='success')
        else:
            flash('Ошибка добавления статьи', category = 'error')
    
    return render_template('add_post.html', title = 'Добавление статьи', menu = dbase.getMenu())

@app.route('/post/<alias>')
def showPost(alias):
    db = get_db()
    dbase = FDataBase(db)
    title, post = dbase.getPost(alias)
    if not title:
        return render_template('page404.html', title='Страница не найдена', menu = dbase.getMenu()), 404
    return render_template('post.html', menu = dbase.getMenu(), title = title, post = post)

@app.errorhandler(404)
def pageNotFound(error):
    return render_template('page404.html', title='Страница не найдена', menu = menu), 404

if __name__ == '__main__':
    app.run(debug=True)

# with app.test_request_context():
#     print(url_for('about'))
#     print(url_for('profile', username = 'boba'))