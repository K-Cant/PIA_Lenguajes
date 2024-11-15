from flask import Flask, jsonify, redirect, render_template, request, session, url_for
import pymysql
import pymysql.cursors
from dbconfig import getDBConnection
from tmdbv3api import TMDb, Movie
from datetime import datetime

tmdb = TMDb()
tmdb.api_key = '4be2ae539f7239f9c10abfa34c1464ce'
tmdb.language = 'es'

app = Flask(__name__)
app.secret_key = "super secret key"

@app.route('/', methods=['GET'])
def home():
    return render_template('sign_in.html')

@app.route('/sign_in', methods=['GET','POST'])
def sign_in():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        email = request.form['email']

        connection = getDBConnection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM usuarios WHERE email =%s", (email))
        user_found = cursor.fetchone()

        if user_found:
            return render_template('sign_in.html', message="El email ya ha sido registrado.")

        try:
            cursor.execute("INSERT INTO usuarios (username, password_user, email) VALUES (%s,%s,%s)", (user, password, email))
            connection.commit()
            return redirect(url_for('login'))
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('sign_in.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
        connection = getDBConnection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND password_user = %s", (email, password))
        user_found = cursor.fetchone()
        cursor.close()

        if user_found is not None:
            session['email'] = email
            session['username'] = user_found['username']

            return redirect(url_for('pelis'))
        else:
            return render_template('login.html', message="Correo o constrasena incorrectos")

    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/pelis', methods=['GET'])
def pelis():
    movie = Movie()
    popular = movie.popular(page=1)

    popular_data = []

    for p in popular:
        movie_data = {
            'id' : p.id,
            'title' : p.title,
            'overview' : p.overview,
            'poster_path' : p.poster_path,
            'vote_average' : p.vote_average
        }
        popular_data.append(movie_data)

    connection = getDBConnection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("SELECT * FROM resena")
        data_resenas = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        data_resenas = []
    finally:
        cursor.close()
        connection.close()

    return render_template('pelis.html', peliculas_populares = popular_data, resenas = data_resenas)

@app.route('/perfil', methods=['GET'])
def perfil():
    email = session['email']
    connection = getDBConnection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("SELECT * FROM resena WHERE email = %s", (email))
        data_resenas = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        data_resenas = []
    finally:
        cursor.close()
        connection.close()

    return render_template('perfil.html', resenas = data_resenas)

@app.route('/act_Data', methods=['POST'])
def act_Data():
    user = request.form['user']
    password = request.form['password']
    email = session['email']

    connection = getDBConnection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("UPDATE usuarios SET username = %s, password_user = %s WHERE email = %s", (user, password, email))
        connection.commit()
        session['username'] = user
        return redirect(url_for('perfil'))
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    return render_template('perfil.html')

@app.route('/nueva_resena', methods=['POST'])
def nueva_resena():
    email = session['email']
    user = session['username']
    titulo = request.form['titulo']
    resena = request.form['resena']
    poster_path = request.form['poster_path']
    d = datetime.now()
    date_resena = d.strftime("%Y-%m-%d %H:%M:%S")

    connection = getDBConnection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("INSERT INTO resena (titulo, resena, date_resena, email, username, poster_path) VALUES (%s,%s,%s, %s, %s, %s)", (titulo, resena, date_resena, email, user, poster_path))
        connection.commit()
        return redirect(url_for('perfil'))
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    return render_template('perfil.html')

@app.route('/delete', methods=['POST'])
def delete():
    id = request.form['id']

    connection = getDBConnection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM resena WHERE id =%s", (id))
        connection.commit()
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    finally :
        cursor.close()
        connection.close()

    return redirect(url_for('perfil'))

@app.route('/editar_resena', methods = ['POST'])
def editar_resena():
    connection = getDBConnection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    id = request.form['id']
    titulo = request.form['titulo']
    resena = request.form['resena']

    try:
        cursor.execute("UPDATE resena SET titulo = %s, resena = %s WHERE id = %s", (titulo, resena, id))
        connection.commit()
        return redirect(url_for('perfil'))
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
        
    return render_template('perfil.html')

@app.route('/search', methods=['GET'])
def search_movies():
    movie = Movie()
    query = request.args.get('query') 
    if query:
        search_results = movie.search(query)
        movie_list = []
        for result in search_results:
            movie_list.append({
                'title': result.title,
                'poster_path': result.poster_path 
            })

        return jsonify(movie_list) 
    return jsonify([]) 
    
if __name__ == '__main__':
    app.run(debug=True)