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
app.secret_key = 'your-super-super-secret-key'  # Required for session encryption

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'securitycats'
}

# In-memory rate limit store: {ip: [datetime, ...]}
comment_rate_limit = {}
login_rate_limit = {}
article_rate_limit = {}
signup_rate_limit = {}

####################################
# ROUTES
###################################    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
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
    csrf_token = secrets.token_hex(32)
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
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM articles")
        articles = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': articles})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_article/<int:article_id>', methods=['GET'])
def get_article_with_comments(article_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM articles WHERE article_id = %s", (article_id,))
        article = cursor.fetchone()
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
    if 'user_id' not in session or session.get('role') != 'admin':
        # Log unauthorized attempt
        ip = request.remote_addr
        now = datetime.utcnow()
        username = session.get('name', 'anonymous')
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO article_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
            (now, ip, username, False, 'Admin access required')
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    
    try:
        ip = request.remote_addr
        now = datetime.utcnow()
        username = session.get('name', 'anonymous')
        
        # Rate limiting: 1 article per minute per IP
        window_start = now - timedelta(minutes=1)
        if ip in article_rate_limit:
            article_rate_limit[ip] = [t for t in article_rate_limit[ip] if t > window_start]
        else:
            article_rate_limit[ip] = []
        if len(article_rate_limit[ip]) >= 1:
            # Log failed attempt due to rate limit
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO article_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
                (now, ip, username, False, 'Rate limit exceeded: max 1 article per minute')
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Rate limit exceeded: max 1 article per minute'}), 429
        article_rate_limit[ip].append(now)

        data = request.get_json()
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')
        
        # Initialize logging variables
        success = False
        error_message = None

        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            error_message = 'Invalid CSRF token'
        elif not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            error_message = 'CSRF token expired'
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
        else:
            # Invalidate token after use
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            atitle = data.get('atitle')
            article = data.get('article')
            def sanitize_article(text):
                allowed = re.compile(r"[^a-zA-Z0-9 .,!?@#\-_'\"\(\)\[\]:;\n]", re.UNICODE)
                text = allowed.sub('', text)
                text = text[:1000]
                return text
            sanitized_title = sanitize_article(atitle) if atitle else ''
            sanitized_article = sanitize_article(article) if article else ''
            if not sanitized_title:
                error_message = 'Article title is required and must contain valid characters'
            elif not sanitized_article:
                error_message = 'Article content is required and must contain valid characters'
            else:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO articles (title, article) VALUES (%s, %s)", (sanitized_title, sanitized_article))
                conn.commit()
                success = True
                error_message = 'Article submitted successfully'
                cursor.close()
                conn.close()

        # Log the article attempt
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO article_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
            (now, ip, username, success, error_message)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if success:
            return jsonify({'status': 'success'})
        else:
            safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', error_message)[:200]
            status_code = 403 if 'CSRF' in error_message else 400
            return jsonify({'status': 'error', 'message': safe_message}), status_code

    except Exception as e:
        safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', str(e))[:200]
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO article_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
            (now, ip, username, False, safe_message)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'error', 'message': safe_message}), 500

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    allowed_roles = ['user', 'moderator', 'admin']
    if session.get('role') not in allowed_roles:
        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403

    try:
        ip = request.remote_addr
        now = datetime.utcnow()
        username = session.get('name', 'anonymous')
        
        # Rate limiting: 5 comment per minute per IP
        window_start = now - timedelta(minutes=1)
        if ip in comment_rate_limit:
            comment_rate_limit[ip] = [t for t in comment_rate_limit[ip] if t > window_start]
        else:
            comment_rate_limit[ip] = []
        if len(comment_rate_limit[ip]) >= 5:
            # Log failed attempt due to rate limit
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comment_attempts (timestamp, ip_address, username, article_id, success, error_message) VALUES (%s, %s, %s, %s, %s, %s)",
                (now, ip, username, None, False, 'Rate limit exceeded: max 5 comments per minute')
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Rate limit exceeded: max 5 comments per minute'}), 429
        comment_rate_limit[ip].append(now)

        data = request.get_json()
        article_id = data.get('article_id')
        comment = data.get('comment')
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')

        # Initialize logging variables
        success = False
        error_message = None
        article_id_int = None

        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            error_message = 'Invalid CSRF token'
        elif not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            error_message = 'CSRF token expired'
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
        elif not article_id:
            error_message = 'Article ID is required'
        else:
            try:
                article_id_int = int(article_id)
                if article_id_int <= 0:
                    error_message = 'Article ID must be a positive integer'
            except (ValueError, TypeError):
                error_message = 'Article ID must be a positive integer'
            if not error_message:
                if not comment:
                    error_message = 'Comment content is required'
                else:
                    allowed = re.compile(r"^[a-zA-Z0-9 .,!?@#\-_'\"\(\)\[\]:;\n]{1,1000}$", re.UNICODE)
                    if not allowed.match(comment):
                        error_message = 'Comment contains invalid characters or is too long (max 1000)'
                    else:
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
                        success = True
                        error_message = 'Comment submitted successfully'
                        cursor.close()
                        conn.close()

        # Log the comment attempt
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comment_attempts (timestamp, ip_address, username, article_id, success, error_message) VALUES (%s, %s, %s, %s, %s, %s)",
            (now, ip, username, article_id_int, success, error_message)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if success:
            return jsonify({'status': 'success', 'message': 'Comment submitted successfully'})
        else:
            safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', error_message)[:200]
            status_code = 403 if 'CSRF' in error_message else 400
            return jsonify({'status': 'error', 'message': safe_message}), status_code

    except Exception as e:
        safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', str(e))[:200]
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comment_attempts (timestamp, ip_address, username, article_id, success, error_message) VALUES (%s, %s, %s, %s, %s, %s)",
            (now, ip, username, None, False, safe_message)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'error', 'message': safe_message}), 500

@app.route('/remove_comment', methods=['POST'])
def remove_comment():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    allowed_roles = ['moderator', 'admin']
    if session.get('role') not in allowed_roles:
        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403

    try:
        data = request.get_json()
        comment_id = data.get('comment_id')
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')

        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 403
        elif not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'error', 'message': 'CSRF token expired'}), 403
        elif not comment_id:
            return jsonify({'status': 'error', 'message': 'Comment ID is required'}), 400

        try:
            comment_id_int = int(comment_id)
            if comment_id_int <= 0:
                return jsonify({'status': 'error', 'message': 'Comment ID must be a positive integer'}), 400
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Comment ID must be a positive integer'}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM comments WHERE comment_id = %s", (comment_id_int,))
        if cursor.rowcount > 0:
            conn.commit()
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'success', 'message': 'Comment removed successfully'})
        else:
            conn.rollback()
            return jsonify({'status': 'error', 'message': 'Comment not found'}), 404
        cursor.close()
        conn.close()

    except Exception as e:
        safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', str(e))[:200]
        return jsonify({'status': 'error', 'message': safe_message}), 500

@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Rate limiting: max 5 signups per 20 minutes per IP
        ip = request.remote_addr
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=20)
        if ip not in signup_rate_limit:
            signup_rate_limit[ip] = []
        signup_rate_limit[ip] = [t for t in signup_rate_limit[ip] if t > window_start]
        if len(signup_rate_limit[ip]) >= 5:
            return jsonify({'status': 'error', 'message': 'Too many signup attempts. Please wait and try again.'}), 429
        signup_rate_limit[ip].append(now)

        data = request.get_json()
        name = data.get('name')
        password = data.get('password')
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')

        # Validate CSRF token
        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 403
        elif not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return jsonify({'status': 'error', 'message': 'CSRF token expired'}), 403

        # Validate inputs
        if not name or not password:
            return jsonify({'status': 'error', 'message': 'Name and password are required'}), 400
        if len(name) > 50 or not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            return jsonify({'status': 'error', 'message': 'Invalid username'}), 400
        if len(password) < 12 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[^a-zA-Z0-9]', password):
            return jsonify({'status': 'error', 'message': 'Password must be at least 12 characters with upper, lower, digit, and special character'}), 400

        # Check if username already exists
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

        # Hash password and insert user with default role 'user'
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute("INSERT INTO users (name, password, role) VALUES (%s, %s, %s)", (name, hashed_password, 'user'))
        conn.commit()
        cursor.close()
        conn.close()

        session.pop('csrf_token', None)
        session.pop('csrf_token_expiry', None)
        return jsonify({'status': 'success', 'message': 'Signup successful'})

    except Exception as e:
        safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', str(e))[:200]
        return jsonify({'status': 'error', 'message': safe_message}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        # Rate limiting: max 5 login attempts per 20 minutes per IP
        ip = request.remote_addr
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=20)
        if ip in login_rate_limit:
            login_rate_limit[ip] = [t for t in login_rate_limit[ip] if t > window_start]
        else:
            login_rate_limit[ip] = []
        if len(login_rate_limit[ip]) >= 5:
            # Log failed attempt due to rate limit
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO login_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
                (now, ip, 'unknown', False, 'Too many login attempts')
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Too many login attempts. Please wait and try again.'}), 429
        login_rate_limit[ip].append(now)

        # Validate CSRF token and expiry
        data = request.get_json()
        client_csrf_token = data.get('csrf_token')
        server_csrf_token = session.get('csrf_token')
        csrf_expiry = session.get('csrf_token_expiry')
        username = data.get('name', 'unknown')

        # Initialize logging variables
        success = False
        error_message = None

        if not client_csrf_token or not server_csrf_token or client_csrf_token != server_csrf_token:
            error_message = 'Invalid CSRF token'
        elif not csrf_expiry or datetime.utcnow().timestamp() > csrf_expiry:
            error_message = 'CSRF token expired'
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
        else:
            # Invalidate token after use
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            name = data.get('name')
            password = data.get('password')
            # Validate username: max 50 chars, allowed charset (alphanumeric, _, ., -)
            if not name or not password:
                error_message = 'Missing name or password'
            elif len(name) > 50:
                error_message = 'Username too long (max 50 characters)'
            elif not re.match(r'^[a-zA-Z0-9_.-]+$', name):
                error_message = 'Username contains invalid characters'
            # Enforce strong password: min 12 chars, must include upper, lower, digit, special
            elif len(password) < 12:
                error_message = 'Password must be at least 12 characters long'
            elif not re.search(r'[A-Z]', password):
                error_message = 'Password must include at least one uppercase letter'
            elif not re.search(r'[a-z]', password):
                error_message = 'Password must include at least one lowercase letter'
            elif not re.search(r'[0-9]', password):
                error_message = 'Password must include at least one digit'
            elif not re.search(r'[^a-zA-Z0-9]', password):
                error_message = 'Password must include at least one special character'
            else:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
                user = cursor.fetchone()
                if user and bcrypt.check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['name'] = user['name']
                    session['role'] = user['role']  # Store the role in session
                    success = True
                    error_message = 'Login successful'
                    # Redirect based on role
                    if user['role'] == 'admin':
                        redirect_url = '/admin'
                    elif user['role'] == 'moderator':
                        redirect_url = '/'  # Adjust as needed for moderator page
                    elif user['role'] == 'user':
                        redirect_url = '/'  # Default to index for users
                    else:
                        redirect_url = '/'  # Default fallback
                else:
                    error_message = 'Invalid username or password'
                cursor.close()
                conn.close()

        # Log the login attempt
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
            (now, ip, username, success, error_message)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if success:
            return jsonify({'status': 'success', 'message': 'Login successful', 'redirect': redirect_url})
        else:
            safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', error_message)[:200]
            status_code = 403 if 'CSRF' in error_message else 401 if 'Invalid username' in error_message else 400
            return jsonify({'status': 'error', 'message': safe_message}), status_code

    except Exception as e:
        safe_message = re.sub(r'[^a-zA-Z0-9 .,!?@#\-_"]', '', str(e))[:200]
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_attempts (timestamp, ip_address, username, success, error_message) VALUES (%s, %s, %s, %s, %s)",
            (datetime.utcnow(), ip, username, False, safe_message)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'error', 'message': safe_message}), 500

if __name__ == '__main__':
    app.run(debug=True)