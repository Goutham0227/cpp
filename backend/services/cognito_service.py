"""
Amazon Cognito Service Wrapper.
Handles freelancer authentication and authorization.
Falls back to local mock mode when USE_AWS is false.
"""

import uuid
import hashlib
from datetime import datetime, timedelta


class CognitoService:
    """Wrapper for Amazon Cognito with local mock fallback."""

    def __init__(self, use_aws=False, region="eu-west-1",
                 user_pool_id="eu-west-1_example", client_id="example-client-id"):
        self.use_aws = use_aws
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self._mock_users = {}
        self._mock_tokens = {}

        if self.use_aws:
            import boto3
            self.client = boto3.client("cognito-idp", region_name=region)
        else:
            self.client = None

    def sign_up(self, username: str, password: str, email: str) -> dict:
        if self.use_aws:
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}],
            )
            return {"user_id": response["UserSub"], "confirmed": False}
        else:
            user_id = str(uuid.uuid4())
            self._mock_users[username] = {
                "user_id": user_id,
                "username": username,
                "password_hash": hashlib.sha256(password.encode()).hexdigest(),
                "email": email,
                "confirmed": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            return {"user_id": user_id, "confirmed": True}

    def sign_in(self, username: str, password: str) -> dict:
        if self.use_aws:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": username, "PASSWORD": password},
            )
            return {
                "access_token": response["AuthenticationResult"]["AccessToken"],
                "id_token": response["AuthenticationResult"]["IdToken"],
                "refresh_token": response["AuthenticationResult"]["RefreshToken"],
            }
        else:
            user = self._mock_users.get(username)
            if not user:
                return {"error": "User not found"}
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            if user["password_hash"] != pw_hash:
                return {"error": "Invalid password"}

            token = f"mock-token-{uuid.uuid4().hex[:16]}"
            self._mock_tokens[token] = {
                "username": username,
                "user_id": user["user_id"],
                "expires": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }
            return {
                "access_token": token,
                "id_token": f"mock-id-{uuid.uuid4().hex[:16]}",
                "refresh_token": f"mock-refresh-{uuid.uuid4().hex[:16]}",
            }

    def verify_token(self, token: str) -> dict:
        if self.use_aws:
            # In production, verify JWT with Cognito
            return {"valid": True, "username": "aws-user"}
        else:
            token_data = self._mock_tokens.get(token)
            if not token_data:
                return {"valid": False, "error": "Invalid token"}
            if datetime.fromisoformat(token_data["expires"]) < datetime.utcnow():
                return {"valid": False, "error": "Token expired"}
            return {"valid": True, "username": token_data["username"], "user_id": token_data["user_id"]}

    def get_user(self, username: str) -> dict:
        if self.use_aws:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=username
            )
            return response
        else:
            user = self._mock_users.get(username)
            if user:
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None

    def get_status(self) -> dict:
        return {
            "service": "Amazon Cognito",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "user_pool_id": self.user_pool_id,
            "registered_users": len(self._mock_users) if not self.use_aws else "N/A",
        }
