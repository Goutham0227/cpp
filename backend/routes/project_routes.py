"""Project CRUD routes."""

from flask import Blueprint, request, jsonify, current_app

project_bp = Blueprint("projects", __name__)


@project_bp.route("/api/projects", methods=["GET"])
def get_projects():
    """List all projects."""
    client_id = request.args.get("client_id")
    if client_id:
        projects = current_app.config["project_model"].get_by_client(client_id)
    else:
        projects = current_app.config["project_model"].get_all()
    return jsonify({"projects": projects, "count": len(projects)}), 200


@project_bp.route("/api/projects", methods=["POST"])
def create_project():
    """Create a new project."""
    data = request.get_json()
    if not data or "name" not in data or "client_id" not in data:
        return jsonify({"error": "name and client_id are required"}), 400
    project = current_app.config["project_model"].create(data)
    current_app.config["cloudwatch"].log_event("projects", f"Created project: {data['name']}")
    return jsonify(project), 201


@project_bp.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """Get a specific project."""
    project = current_app.config["project_model"].get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project), 200


@project_bp.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    """Update a project."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    existing = current_app.config["project_model"].get(project_id)
    if not existing:
        return jsonify({"error": "Project not found"}), 404
    project = current_app.config["project_model"].update(project_id, data)
    return jsonify(project), 200


@project_bp.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project."""
    existing = current_app.config["project_model"].get(project_id)
    if not existing:
        return jsonify({"error": "Project not found"}), 404
    current_app.config["project_model"].delete(project_id)
    return jsonify({"message": "Project deleted"}), 200
