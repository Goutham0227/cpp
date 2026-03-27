"""Client CRUD routes."""

from flask import Blueprint, request, jsonify, current_app

client_bp = Blueprint("clients", __name__)


@client_bp.route("/api/clients", methods=["GET"])
def get_clients():
    """List all clients."""
    clients = current_app.config["client_model"].get_all()
    return jsonify({"clients": clients, "count": len(clients)}), 200


@client_bp.route("/api/clients", methods=["POST"])
def create_client():
    """Create a new client."""
    data = request.get_json()
    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "name and email are required"}), 400
    client = current_app.config["client_model"].create(data)
    current_app.config["cloudwatch"].log_event("clients", f"Created client: {data['name']}")
    return jsonify(client), 201


@client_bp.route("/api/clients/<client_id>", methods=["GET"])
def get_client(client_id):
    """Get a specific client."""
    client = current_app.config["client_model"].get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client), 200


@client_bp.route("/api/clients/<client_id>", methods=["PUT"])
def update_client(client_id):
    """Update a client."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    existing = current_app.config["client_model"].get(client_id)
    if not existing:
        return jsonify({"error": "Client not found"}), 404
    client = current_app.config["client_model"].update(client_id, data)
    return jsonify(client), 200


@client_bp.route("/api/clients/<client_id>", methods=["DELETE"])
def delete_client(client_id):
    """Delete a client."""
    existing = current_app.config["client_model"].get(client_id)
    if not existing:
        return jsonify({"error": "Client not found"}), 404
    current_app.config["client_model"].delete(client_id)
    return jsonify({"message": "Client deleted"}), 200
