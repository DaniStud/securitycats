from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow CORS for all routes

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'securitycats'
}

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
    
    
if __name__ == '__main__':
    app.run(debug=True)