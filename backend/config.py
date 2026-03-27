"""
Application configuration for Flask backend.
Supports local (SQLite) and production (AWS) modes.
"""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-goutham-25167936")
    USE_AWS = os.environ.get("USE_AWS", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "timetracker.db")

    # AWS Configuration
    AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
    DYNAMODB_TABLE_PREFIX = os.environ.get("DYNAMODB_TABLE_PREFIX", "timetracker_")
    S3_BUCKET = os.environ.get("S3_BUCKET", "timetracker-invoices-25167936")
    COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "eu-west-1_example")
    COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "example-client-id")
    CLOUDWATCH_NAMESPACE = os.environ.get("CLOUDWATCH_NAMESPACE", "TimeTracker")
    LAMBDA_FUNCTION_NAME = os.environ.get("LAMBDA_FUNCTION_NAME", "invoice-generator")
    API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "https://api.example.com")

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration - local mock mode."""
    DEBUG = True
    USE_AWS = False


class ProductionConfig(Config):
    """Production configuration - real AWS services."""
    USE_AWS = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    USE_AWS = False
    DATABASE_PATH = ":memory:"


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    return configs.get(env, DevelopmentConfig)
