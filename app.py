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
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-super-secret-key'  # Required for session encryption


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'securitycats'
}


# In-memory rate limit store: {ip: [datetime, ...]}
comment_rate_limit = {}

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
    csrf_token = secrets.token_hex(32)
    session['csrf_token'] = csrf_token
    session['csrf_token_expiry'] = (datetime.utcnow() + timedelta(minutes=30)).timestamp()
    return render_template('admin.html', csrf_token=csrf_token)

@app.route('/logout')
def logout():
    session.clear()
    return "<h1>Logged out</h1><p><a href='/login_page'>Go back to login</a></p>"


@app.route('/login_page')
def login_page():
    # generate token, store in session
    csrf_token = secrets.token_hex(32) #generate secure random token
    session['csrf_token'] = csrf_token
    session['csrf_token_expiry'] = (datetime.utcnow() + timedelta(minutes=30)).timestamp()
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
            # Generate CSRF token and set expiry
            csrf_token = secrets.token_hex(32)
            session['csrf_token'] = csrf_token
            session['csrf_token_expiry'] = (datetime.utcnow() + timedelta(minutes=30)).timestamp()
            return render_template('article.html', article=article, csrf_token=csrf_token)
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
        # Validate CSRF token and expiry
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')
        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 403
        if not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'error', 'message': 'CSRF token expired'}), 403
        # Invalidate token after use
        session.pop('csrf_token', None)
        session.pop('csrf_token_expiry', None)

        atitle = data.get('atitle')
        article = data.get('article')
        # Sanitize article title and content (same as sanitize_comment)
        def sanitize_article(text):
            allowed = re.compile(r"[^a-zA-Z0-9 .,!?@#\-_'\"\(\)\[\]:;\n]", re.UNICODE)
            text = allowed.sub('', text)
            text = text[:1000]
            return text
        sanitized_title = sanitize_article(atitle) if atitle else ''
        sanitized_article = sanitize_article(article) if article else ''
        # Validate input for empty or invalid values after sanitization
        if not sanitized_title:
            return jsonify({'status': 'error', 'message': 'Article title is required and must contain valid characters'}), 400
        if not sanitized_article:
            return jsonify({'status': 'error', 'message': 'Article content is required and must contain valid characters'}), 400
        # Use parameterized queries for database insert
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO articles (title, article) VALUES (%s, %s)", (sanitized_title, sanitized_article))
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
        ip = request.remote_addr
        now = datetime.utcnow()
        # Clean up old entries
        window_start = now - timedelta(hours=1)
        if ip in comment_rate_limit:
            # Remove timestamps older than 1 hour
            comment_rate_limit[ip] = [t for t in comment_rate_limit[ip] if t > window_start]
        else:
            comment_rate_limit[ip] = []
        if len(comment_rate_limit[ip]) >= 20:
            return jsonify({'status': 'error', 'message': 'Rate limit exceeded: max 20 comments per hour per IP'}), 429
        # Add this comment's timestamp
        comment_rate_limit[ip].append(now)
        
        data = request.get_json()
        article_id = data.get('article_id')
        comment = data.get('comment')
        client_csrf_token = data.get('csrf_token')

        # CSRF token validation
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')
        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 403
        if not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'error', 'message': 'CSRF token expired'}), 403
        # Invalidate token after use
        session.pop('csrf_token', None)
        session.pop('csrf_token_expiry', None)

        # Ensure article_id and comment are provided
        if not article_id:
            return jsonify({'status': 'error', 'message': 'Article ID is required'}), 400
        # Validate article_id is a positive integer
        try:
            article_id_int = int(article_id)
            if article_id_int <= 0:
                return jsonify({'status': 'error', 'message': 'Article ID must be a positive integer'}), 400
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Article ID must be a positive integer'}), 400
        if not comment:
            return jsonify({'status': 'error', 'message': 'Comment content is required'}), 400
        # Validate comment content: must be 1-1000 chars, only allowed signs
        allowed = re.compile(r"^[a-zA-Z0-9 .,!?@#\-_'\"\(\)\[\]:;\n]{1,1000}$", re.UNICODE)
        if not allowed.match(comment):
            return jsonify({'status': 'error', 'message': 'Comment contains invalid characters or is too long (max 1000)'}), 400
        def sanitize_comment(comment):
            allowed = re.compile(r"[^a-zA-Z0-9 .,!?@#\-_'\"\(\)\[\]:;\n]", re.UNICODE)
            comment = allowed.sub('', comment)
            comment = comment[:1000]
            return comment
        sanitized_comment = sanitize_comment(comment)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (article_id, content) VALUES (%s, %s)", (article_id_int, sanitized_comment))
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
        # Validate CSRF token and expiry
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')
        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            return jsonify({'status': 'error', 'message': 'invalid CSRF token'}), 403
        if not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'error', 'message': 'CSRF token expired'}), 403
        # Invalidate token after use
        session.pop('csrf_token', None)
        session.pop('csrf_token_expiry', None)
        name = data.get('name')
        password = data.get('password')
        # Validate username: max 50 chars, allowed charset
        if not name or not password:
            return jsonify({'status': 'error', 'message': 'Missing name or password'}), 400
        if len(name) > 50:
            return jsonify({'status': 'error', 'message': 'Username too long (max 50 characters)'}), 400
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            return jsonify({'status': 'error', 'message': 'Username contains invalid characters'}), 400
        # Use parameterized query for DB access
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
            return jsonify({'status': 'success', 'message': 'Login successful'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    
if __name__ == '__main__':
    app.run(debug=True)