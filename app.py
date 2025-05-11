from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from flask import render_template

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow CORS for all routes

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'securitycats'
}



####################################
#ROUTES
###################################
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
    
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


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
def get_article(article_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM articles WHERE article_id = %s", (article_id,))
        article = cursor.fetchone()
        cursor.close()
        conn.close()

        if article:
            return jsonify({'status': 'success', 'data': article})
        else:
            return jsonify({'status': 'error', 'message': 'Article not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    
@app.route('/get_comments/<int:article_id>', methods=['GET'])
def get_comments(article_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM comments WHERE article_id = %s", (article_id,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success', 'data': comments})

    
    
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

@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.get_json()
    article_id = data.get('article_id')
    author = data.get('author', 'Anonymous')
    content = data.get('content')

    if not article_id or not content:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (article_id, author, content) VALUES (%s, %s, %s)",
        (article_id, author, content)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success'})

    
if __name__ == '__main__':
    app.run(debug=True)