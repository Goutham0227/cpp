"""Time Entry CRUD routes."""

from flask import Blueprint, request, jsonify, current_app

time_entry_bp = Blueprint("time_entries", __name__)


@time_entry_bp.route("/api/time-entries", methods=["GET"])
def get_time_entries():
    """List all time entries."""
    project_id = request.args.get("project_id")
    if project_id:
        entries = current_app.config["time_entry_model"].get_by_project(project_id)
    else:
        entries = current_app.config["time_entry_model"].get_all()
    return jsonify({"time_entries": entries, "count": len(entries)}), 200


@time_entry_bp.route("/api/time-entries", methods=["POST"])
def create_time_entry():
    """Create a new time entry."""
    data = request.get_json()
    if not data or "project_id" not in data:
        return jsonify({"error": "project_id is required"}), 400
    entry = current_app.config["time_entry_model"].create(data)
    current_app.config["cloudwatch"].put_metric("TimeEntriesCreated", 1)
    return jsonify(entry), 201


@time_entry_bp.route("/api/time-entries/<entry_id>", methods=["GET"])
def get_time_entry(entry_id):
    """Get a specific time entry."""
    entry = current_app.config["time_entry_model"].get(entry_id)
    if not entry:
        return jsonify({"error": "Time entry not found"}), 404
    return jsonify(entry), 200


@time_entry_bp.route("/api/time-entries/<entry_id>", methods=["PUT"])
def update_time_entry(entry_id):
    """Update a time entry."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    existing = current_app.config["time_entry_model"].get(entry_id)
    if not existing:
        return jsonify({"error": "Time entry not found"}), 404
    entry = current_app.config["time_entry_model"].update(entry_id, data)
    return jsonify(entry), 200


@time_entry_bp.route("/api/time-entries/<entry_id>", methods=["DELETE"])
def delete_time_entry(entry_id):
    """Delete a time entry."""
    existing = current_app.config["time_entry_model"].get(entry_id)
    if not existing:
        return jsonify({"error": "Time entry not found"}), 404
    current_app.config["time_entry_model"].delete(entry_id)
    return jsonify({"message": "Time entry deleted"}), 200
