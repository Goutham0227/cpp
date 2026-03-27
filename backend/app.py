"""
Flask application factory for Freelancer Time Tracking & Invoice Generator.

Student: Goutham Uppu (25167936)
Module: Cloud Platform Programming, NCI
"""

from flask import Flask
from flask_cors import CORS
from config import get_config
from models import Database, ClientModel, ProjectModel, TimeEntryModel, InvoiceModel
from services import (
    DynamoDBService, S3Service, LambdaService,
    APIGatewayService, CognitoService, CloudWatchService, TextractService,
)
from routes import client_bp, project_bp, time_entry_bp, invoice_bp, aws_bp


def create_app(config_class=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(get_config())

    # Enable CORS
    CORS(app)

    # Initialize database
    db_path = app.config.get("DATABASE_PATH", "timetracker.db")
    db = Database(db_path)

    # Initialize models
    app.config["db"] = db
    app.config["client_model"] = ClientModel(db)
    app.config["project_model"] = ProjectModel(db)
    app.config["time_entry_model"] = TimeEntryModel(db)
    app.config["invoice_model"] = InvoiceModel(db)

    # Initialize AWS services (all in mock mode locally)
    use_aws = app.config.get("USE_AWS", False)
    app.config["dynamodb"] = DynamoDBService(use_aws=use_aws)
    app.config["s3_service"] = S3Service(use_aws=use_aws)
    app.config["lambda_service"] = LambdaService(use_aws=use_aws)
    app.config["api_gateway"] = APIGatewayService(use_aws=use_aws)
    app.config["cognito"] = CognitoService(use_aws=use_aws)
    app.config["cloudwatch"] = CloudWatchService(use_aws=use_aws)
    app.config["textract"] = TextractService(use_aws=use_aws)

    # Register blueprints
    app.register_blueprint(client_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(time_entry_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(aws_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("Freelancer Time Tracking & Invoice Generator")
    print("Student: Goutham Uppu (25167936)")
    print("Module: Cloud Platform Programming, NCI")
    print("Running in LOCAL MOCK mode (all AWS services mocked)")
    print("=" * 60)
    app.run(debug=True, port=5000)
