"""
Amazon DynamoDB Service Wrapper.
Handles data persistence for time entries, clients, and invoices.
Falls back to local mock mode when USE_AWS is false.
"""

import uuid
from datetime import datetime


class DynamoDBService:
    """Wrapper for Amazon DynamoDB with local mock fallback."""

    def __init__(self, use_aws=False, region="eu-west-1", table_prefix="timetracker_"):
        self.use_aws = use_aws
        self.region = region
        self.table_prefix = table_prefix
        self._mock_tables = {}

        if self.use_aws:
            import boto3
            self.client = boto3.resource("dynamodb", region_name=region)
        else:
            self.client = None

    def _get_mock_table(self, table_name):
        full_name = f"{self.table_prefix}{table_name}"
        if full_name not in self._mock_tables:
            self._mock_tables[full_name] = {}
        return self._mock_tables[full_name]

    def put_item(self, table_name: str, item: dict) -> dict:
        if self.use_aws:
            table = self.client.Table(f"{self.table_prefix}{table_name}")
            table.put_item(Item=item)
            return item
        else:
            mock_table = self._get_mock_table(table_name)
            key = item.get("id", item.get("client_id", item.get("entry_id", str(uuid.uuid4()))))
            mock_table[key] = item
            return item

    def get_item(self, table_name: str, key: dict) -> dict:
        if self.use_aws:
            table = self.client.Table(f"{self.table_prefix}{table_name}")
            response = table.get_item(Key=key)
            return response.get("Item")
        else:
            mock_table = self._get_mock_table(table_name)
            key_val = list(key.values())[0]
            return mock_table.get(key_val)

    def scan_table(self, table_name: str) -> list:
        if self.use_aws:
            table = self.client.Table(f"{self.table_prefix}{table_name}")
            response = table.scan()
            return response.get("Items", [])
        else:
            mock_table = self._get_mock_table(table_name)
            return list(mock_table.values())

    def delete_item(self, table_name: str, key: dict) -> bool:
        if self.use_aws:
            table = self.client.Table(f"{self.table_prefix}{table_name}")
            table.delete_item(Key=key)
            return True
        else:
            mock_table = self._get_mock_table(table_name)
            key_val = list(key.values())[0]
            if key_val in mock_table:
                del mock_table[key_val]
                return True
            return False

    def update_item(self, table_name: str, key: dict, updates: dict) -> dict:
        if self.use_aws:
            table = self.client.Table(f"{self.table_prefix}{table_name}")
            expr_parts = []
            expr_values = {}
            expr_names = {}
            for i, (k, v) in enumerate(updates.items()):
                expr_parts.append(f"#attr{i} = :val{i}")
                expr_values[f":val{i}"] = v
                expr_names[f"#attr{i}"] = k
            table.update_item(
                Key=key,
                UpdateExpression="SET " + ", ".join(expr_parts),
                ExpressionAttributeValues=expr_values,
                ExpressionAttributeNames=expr_names,
            )
            return self.get_item(table_name, key)
        else:
            mock_table = self._get_mock_table(table_name)
            key_val = list(key.values())[0]
            if key_val in mock_table:
                mock_table[key_val].update(updates)
                return mock_table[key_val]
            return None

    def get_status(self) -> dict:
        return {
            "service": "Amazon DynamoDB",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "region": self.region,
            "tables": len(self._mock_tables) if not self.use_aws else "N/A",
        }
