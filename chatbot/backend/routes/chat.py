from flask import Blueprint, request, jsonify

chat_routes = Blueprint('chat_routes', __name__)

@chat_routes.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("Received message:", request.json)  # Debug print
        message = request.json.get('message', '')
        response = f"Echo: {message}"
        print("Sending response:", response)  # Debug print
        return jsonify({'response': response})
    except Exception as e:
        print("Error in /api/chat:", str(e))  # Debug print
        return jsonify({'error': str(e)}), 500
