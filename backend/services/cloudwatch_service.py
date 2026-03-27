"""
Amazon CloudWatch Service Wrapper.
Handles billing alerts and application monitoring.
Falls back to local mock mode when USE_AWS is false.
"""

from datetime import datetime
from collections import defaultdict


class CloudWatchService:
    """Wrapper for Amazon CloudWatch with local mock fallback."""

    def __init__(self, use_aws=False, region="eu-west-1", namespace="TimeTracker"):
        self.use_aws = use_aws
        self.region = region
        self.namespace = namespace
        self._mock_metrics = defaultdict(list)
        self._mock_alarms = []
        self._mock_logs = []

        if self.use_aws:
            import boto3
            self.client = boto3.client("cloudwatch", region_name=region)
            self.logs_client = boto3.client("logs", region_name=region)
        else:
            self.client = None

    def put_metric(self, metric_name: str, value: float, unit: str = "Count") -> dict:
        if self.use_aws:
            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Timestamp": datetime.utcnow(),
                }],
            )
            return {"status": "published"}
        else:
            entry = {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._mock_metrics[metric_name].append(entry)
            return {"status": "mock_published", "entry": entry}

    def get_metrics(self, metric_name: str = None) -> list:
        if self.use_aws:
            response = self.client.list_metrics(Namespace=self.namespace)
            return response.get("Metrics", [])
        else:
            if metric_name:
                return self._mock_metrics.get(metric_name, [])
            all_metrics = []
            for entries in self._mock_metrics.values():
                all_metrics.extend(entries)
            return all_metrics

    def create_billing_alarm(self, alarm_name: str, threshold: float,
                              email: str = "") -> dict:
        if self.use_aws:
            self.client.put_metric_alarm(
                AlarmName=alarm_name,
                Namespace="AWS/Billing",
                MetricName="EstimatedCharges",
                Threshold=threshold,
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=1,
                Period=21600,
                Statistic="Maximum",
                ActionsEnabled=True,
            )
            return {"alarm_name": alarm_name, "status": "created"}
        else:
            alarm = {
                "alarm_name": alarm_name,
                "threshold": threshold,
                "email": email,
                "status": "OK",
                "created_at": datetime.utcnow().isoformat(),
            }
            self._mock_alarms.append(alarm)
            return {"alarm_name": alarm_name, "status": "mock_created"}

    def get_alarms(self) -> list:
        if self.use_aws:
            response = self.client.describe_alarms()
            return response.get("MetricAlarms", [])
        return self._mock_alarms

    def log_event(self, log_group: str, message: str) -> dict:
        if self.use_aws:
            pass  # Would use CloudWatch Logs
        entry = {
            "log_group": log_group,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._mock_logs.append(entry)
        return entry

    def get_logs(self, log_group: str = None) -> list:
        if log_group:
            return [l for l in self._mock_logs if l["log_group"] == log_group]
        return self._mock_logs

    def get_status(self) -> dict:
        return {
            "service": "Amazon CloudWatch",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "namespace": self.namespace,
            "metrics_recorded": sum(len(v) for v in self._mock_metrics.values()),
            "alarms": len(self._mock_alarms),
            "log_entries": len(self._mock_logs),
        }
