from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/add', methods=['POST'])
def add_numbers():
    data = request.get_json()
    number1 = data.get('number1')
    number2 = data.get('number2')
    result = number1 + number2
    return jsonify(result=result)

if __name__ == '__main__':
    app.run(debug=True)
