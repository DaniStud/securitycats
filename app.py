from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
import mysql.connector
from flask import render_template
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
from flask import session
import re
import os 
import secrets

app = Flask(__name__)
app.secret_key = 'your-super-secret-key'  # Required for session encryption


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'securitycats'
}


####################################
#ROUTES
###################################    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('admin.html')


@app.route('/logout')
def logout():
    session.clear()
    return "<h1>Logged out</h1><p><a href='/login_page'>Go back to login</a></p>"


@app.route('/login_page')
def login_page():
    # generate token, store in session
    csrf_token = secrets.token_hex(32) #generate secure random token
    session['csrf_token'] = csrf_token
    return render_template('login.html', csrf_token=csrf_token)


@app.route('/article/<int:article_id>')
def render_article(article_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM articles WHERE article_id = %s", (article_id,))
        article = cursor.fetchone()
        cursor.close()
        conn.close()

        if article:
            return render_template('article.html', article=article)
        else:
            return "<h1>404 - Article not found</h1>", 404
    except Exception as e:
        return f"<h1>500 - Server Error</h1><p>{e}</p>", 500
    

    ###########################################
    # GET
    ###########################################
@app.route('/get_articles', methods=['GET'])
def get_articles():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # Use dictionary=True to get column names as keys
        cursor.execute("SELECT * FROM articles")  # Fetch all articles
        articles = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': articles})
    except Exception as e:
        # Handle any server-side errors
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    
    

@app.route('/get_article/<int:article_id>', methods=['GET'])
def get_article_with_comments(article_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch the article
        cursor.execute("SELECT * FROM articles WHERE article_id = %s", (article_id,))
        article = cursor.fetchone()

        # Fetch the comments for the article
        cursor.execute("SELECT * FROM comments WHERE article_id = %s", (article_id,))
        comments = cursor.fetchall()

        cursor.close()
        conn.close()

        if article:
            return jsonify({
                'status': 'success',
                'data': {
                    'article': article,
                    'comments': comments
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Article not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    
    ###########################################
    # POST
    ###########################################
    
    
@app.route('/submit_article', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        atitle = data.get('atitle')
        article = data.get('article')

        # Ensure atitle is provided
        if not atitle:
            return jsonify({'status': 'error', 'message': 'Article title is required'}), 400
        if not article:
            return jsonify({'status': 'error', 'message': 'Article content is required'}), 400
        

        # Connect to the database and insert the article title
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO articles (title, article) VALUES (%s, %s)", (atitle, article))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success'})
    except Exception as e:
        # Handle any server-side errors
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        comment = data.get('comment')

        # Ensure article_id and comment are provided
        if not article_id:
            return jsonify({'status': 'error', 'message': 'Article ID is required'}), 400
        if not comment:
            return jsonify({'status': 'error', 'message': 'Comment content is required'}), 400

        # Custom sanitization function
        def sanitize_comment(comment):
            # Strip HTML tags using regex (allow only plain text)
            comment = re.sub(r'<[^>]+>', '', comment)
            # Remove dangerous attributes and script content
            comment = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', comment, flags=re.IGNORECASE)
            # Limit comment length (e.g., 1000 characters)
            comment = comment[:1000]
            # Escape special characters to prevent injection in display
            html_escape_table = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;'
            }
            return ''.join(html_escape_table.get(c, c) for c in comment)

        sanitized_comment = sanitize_comment(comment)

        # Connect to the database and insert the sanitized comment
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (article_id, content) VALUES (%s, %s)", (article_id, sanitized_comment))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Comment submitted successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        #validate csrf token
        client_csrf_token = data.get('csrf_token')
        if not client_csrf_token or client_csrf_token != session.get('csrf_token'):
            return jsonify({'status': 'error', 'message': 'invalid CSRF token'}), 403
        
        name = data.get('name')
        password = data.get('password')

        if not name or not password:
            return jsonify({'status': 'error', 'message': 'Missing name or password'}), 400

        # Connect to DB and get user by name
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            #clear csrf token to prevent re-use
            session.pop('csrf_token', None)
            return jsonify({'status': 'success', 'message': 'Login successful'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    
if __name__ == '__main__':
    app.run(debug=True)