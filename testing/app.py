from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="flask_chat",
        user="postgres",
        password="omkar@2006"
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to send a message
@app.route('/send', methods=['POST'])
def send_message():
    sender = request.form.get('sender')
    receiver = request.form.get('receiver')
    content = request.form.get('content')
    

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO messages (sender, receiver, content) VALUES (%s, %s, %s)',
        (sender, receiver, content)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'success'})

# Endpoint to fetch new messages
@app.route('/messages')
def get_messages():
    user_a = request.args.get('sender')
    user_b = request.args.get('receiver')
    # RealDictCursor allows us to get results as dictionaries (perfect for JSON)

    if not user_a or not user_b:
        return jsonify([])
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT sender, receiver, content, created_at from messages
        where (sender = %s and receiver = %s)
            or (sender = %s and receiver = %s)
        order by created_at ASC
    """
    
    # Grab the last 50 messages
    cur.execute(query, (user_a, user_b, user_b, user_a))
    messages = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Format the datetime for JSON
    for msg in messages:
        msg['created_at'] = msg['created_at'].strftime('%H:%M:%S')
        
    return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True)
