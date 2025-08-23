"""
Test suite for monitoring and observability features.
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from monitoring import (
    MetricsCollector, AlertManager, HealthChecker, HealthStatus, 
    ApplicationMonitor, Alert, AlertLevel, Metric, HealthCheck
)

class TestMetricsCollector:
    """Test the MetricsCollector class."""
    
    def test_record_metric_basic(self):
        """Test basic metric recording."""
        collector = MetricsCollector(retention_minutes=1)
        
        collector.record("test.metric", 42.5, tags={"env": "test"})
        
        metrics = collector.get_metrics("test.metric")
        assert len(metrics) == 1
        assert metrics[0].name == "test.metric"
        assert metrics[0].value == 42.5
        assert metrics[0].tags == {"env": "test"}
    
    def test_record_metric_multiple(self):
        """Test recording multiple metrics."""
        collector = MetricsCollector(retention_minutes=1)
        
        for i in range(5):
            collector.record("test.counter", i, tags={"iteration": str(i)})
        
        metrics = collector.get_metrics("test.counter")
        assert len(metrics) == 5
        
        # Check values are recorded correctly
        values = [m.value for m in metrics]
        assert values == [0, 1, 2, 3, 4]
    
    def test_get_summary(self):
        """Test metric summary calculations."""
        collector = MetricsCollector(retention_minutes=1)
        
        # Record some test data
        values = [10, 20, 30, 40, 50]
        for value in values:
            collector.record("test.summary", value)
        
        summary = collector.get_summary("test.summary")
        assert summary["count"] == 5
        assert summary["min"] == 10
        assert summary["max"] == 50
        assert summary["avg"] == 30.0
        assert summary["sum"] == 150
        assert summary["latest"] == 50
    
    def test_time_filtering(self):
        """Test time-based metric filtering."""
        collector = MetricsCollector(retention_minutes=60)
        
        # Create a metric with current timestamp
        collector.record("test.time", 100)
        
        # Should find metric when looking at recent data
        recent_metrics = collector.get_metrics("test.time", since_minutes=1)
        assert len(recent_metrics) == 1
        
        # Should not find metric when looking at very old data
        old_metrics = collector.get_metrics("test.time", since_minutes=0)
        assert len(old_metrics) == 0

class TestAlertManager:
    """Test the AlertManager class."""
    
    def test_send_alert_basic(self):
        """Test basic alert sending."""
        manager = AlertManager()
        handler_calls = []
        
        def test_handler(alert):
            handler_calls.append(alert)
        
        manager.add_alert_handler(test_handler)
        
        alert = Alert(
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="This is a test",
            timestamp=datetime.now(timezone.utc),
            context={"key": "value"}
        )
        
        manager.send_alert(alert)
        
        assert len(handler_calls) == 1
        assert handler_calls[0].title == "Test Alert"
        assert handler_calls[0].level == AlertLevel.WARNING
    
    def test_alert_simplified_interface(self):
        """Test the simplified alert interface."""
        manager = AlertManager()
        handler_calls = []
        
        def test_handler(alert):
            handler_calls.append(alert)
        
        manager.add_alert_handler(test_handler)
        
        manager.alert(
            AlertLevel.ERROR,
            "Simple Alert",
            "Simple message",
            context={"error_code": 500},
            tags=["test", "simple"]
        )
        
        assert len(handler_calls) == 1
        alert = handler_calls[0]
        assert alert.level == AlertLevel.ERROR
        assert alert.title == "Simple Alert"
        assert alert.message == "Simple message"
        assert alert.context == {"error_code": 500}
        assert alert.tags == ["test", "simple"]
    
    def test_get_alerts_filtering(self):
        """Test alert filtering by level and time."""
        manager = AlertManager()
        
        # Send different types of alerts
        manager.alert(AlertLevel.INFO, "Info Alert", "Info message")
        manager.alert(AlertLevel.WARNING, "Warning Alert", "Warning message")
        manager.alert(AlertLevel.ERROR, "Error Alert", "Error message")
        
        # Test filtering by level
        error_alerts = manager.get_alerts(level=AlertLevel.ERROR)
        assert len(error_alerts) == 1
        assert error_alerts[0].level == AlertLevel.ERROR
        
        warning_alerts = manager.get_alerts(level=AlertLevel.WARNING)
        assert len(warning_alerts) == 1
        assert warning_alerts[0].level == AlertLevel.WARNING
        
        # Test getting all alerts
        all_alerts = manager.get_alerts()
        assert len(all_alerts) == 3

class TestHealthChecker:
    """Test the HealthChecker class."""
    
    def test_register_and_run_check(self):
        """Test registering and running health checks."""
        checker = HealthChecker()
        
        def healthy_check():
            return HealthCheck(
                name="test_check",
                status=HealthStatus.HEALTHY,
                message="All good",
                duration_ms=10.0,
                timestamp=datetime.now(timezone.utc)
            )
        
        checker.register_check("test_check", healthy_check)
        
        # Run the check
        result = asyncio.run(checker.run_check("test_check"))
        
        assert result.name == "test_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.duration_ms >= 0
    
    def test_failing_health_check(self):
        """Test health check that raises an exception."""
        checker = HealthChecker()
        
        def failing_check():
            raise Exception("Something went wrong")
        
        checker.register_check("failing_check", failing_check)
        
        result = asyncio.run(checker.run_check("failing_check"))
        
        assert result.name == "failing_check"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Something went wrong" in result.message
        assert result.duration_ms >= 0
    
    @pytest.mark.asyncio
    async def test_async_health_check(self):
        """Test asynchronous health checks."""
        checker = HealthChecker()
        
        async def async_check():
            await asyncio.sleep(0.01)  # Simulate async work
            return HealthCheck(
                name="async_check",
                status=HealthStatus.HEALTHY,
                message="Async all good",
                duration_ms=0,
                timestamp=datetime.now(timezone.utc)
            )
        
        checker.register_check("async_check", async_check)
        
        result = await checker.run_check("async_check")
        
        assert result.name == "async_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Async all good"
        assert result.duration_ms >= 10  # Should have some duration from sleep
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all registered checks."""
        checker = HealthChecker()
        
        def healthy_check():
            return HealthCheck(
                name="healthy",
                status=HealthStatus.HEALTHY,
                message="OK",
                duration_ms=0,
                timestamp=datetime.now(timezone.utc)
            )
        
        def degraded_check():
            return HealthCheck(
                name="degraded",
                status=HealthStatus.DEGRADED,
                message="Slow",
                duration_ms=0,
                timestamp=datetime.now(timezone.utc)
            )
        
        checker.register_check("healthy", healthy_check)
        checker.register_check("degraded", degraded_check)
        
        results = await checker.run_all_checks()
        
        assert len(results) == 2
        assert "healthy" in results
        assert "degraded" in results
        assert results["healthy"].status == HealthStatus.HEALTHY
        assert results["degraded"].status == HealthStatus.DEGRADED
    
    def test_overall_status_calculation(self):
        """Test overall status calculation logic."""
        checker = HealthChecker()
        
        # No checks - should be unhealthy
        assert checker.get_overall_status() == HealthStatus.UNHEALTHY
        
        # All healthy
        checker.last_results = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "OK", 0, datetime.now(timezone.utc)),
            "check2": HealthCheck("check2", HealthStatus.HEALTHY, "OK", 0, datetime.now(timezone.utc))
        }
        assert checker.get_overall_status() == HealthStatus.HEALTHY
        
        # Mixed healthy and degraded
        checker.last_results = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "OK", 0, datetime.now(timezone.utc)),
            "check2": HealthCheck("check2", HealthStatus.DEGRADED, "Slow", 0, datetime.now(timezone.utc))
        }
        assert checker.get_overall_status() == HealthStatus.DEGRADED
        
        # Any unhealthy makes overall unhealthy
        checker.last_results = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "OK", 0, datetime.now(timezone.utc)),
            "check2": HealthCheck("check2", HealthStatus.UNHEALTHY, "Failed", 0, datetime.now(timezone.utc))
        }
        assert checker.get_overall_status() == HealthStatus.UNHEALTHY

class TestApplicationMonitor:
    """Test the ApplicationMonitor class."""
    
    def test_record_operation_success(self):
        """Test recording successful operations."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        monitor = ApplicationMonitor(metrics, alerts)
        
        monitor.record_operation("test_operation", success=True, duration_seconds=1.5)
        
        # Check metrics were recorded
        operation_metrics = metrics.get_metrics("app.operation.count")
        duration_metrics = metrics.get_metrics("app.operation.duration_seconds")
        
        assert len(operation_metrics) == 1
        assert len(duration_metrics) == 1
        
        assert operation_metrics[0].tags["operation"] == "test_operation"
        assert operation_metrics[0].tags["success"] == "True"
        assert duration_metrics[0].value == 1.5
    
    def test_record_operation_failure(self):
        """Test recording failed operations."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        monitor = ApplicationMonitor(metrics, alerts)
        
        monitor.record_operation("test_operation", success=False, duration_seconds=0.5)
        
        # Check metrics were recorded
        operation_metrics = metrics.get_metrics("app.operation.count")
        
        assert len(operation_metrics) == 1
        assert operation_metrics[0].tags["success"] == "False"
        
        # Check error count was incremented
        assert monitor.error_counts["test_operation"] == 1
    
    def test_high_error_rate_alert(self):
        """Test that high error rates trigger alerts."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        alert_calls = []
        
        def capture_alert(alert):
            alert_calls.append(alert)
        
        alerts.add_alert_handler(capture_alert)
        monitor = ApplicationMonitor(metrics, alerts)
        
        # Record many failures to trigger high error rate
        for _ in range(8):  # 8 failures
            monitor.record_operation("failing_operation", success=False)
        
        for _ in range(2):  # 2 successes (total 10 operations, 80% error rate)
            monitor.record_operation("failing_operation", success=True)
        
        # Should have triggered an alert for high error rate
        error_alerts = [a for a in alert_calls if "High Error Rate" in a.title]
        assert len(error_alerts) >= 1
        
        alert = error_alerts[0]
        assert alert.level == AlertLevel.ERROR
        assert "failing_operation" in alert.message
    
    def test_slow_operation_alert(self):
        """Test that slow operations trigger alerts."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        alert_calls = []
        
        def capture_alert(alert):
            alert_calls.append(alert)
        
        alerts.add_alert_handler(capture_alert)
        monitor = ApplicationMonitor(metrics, alerts)
        
        # Record a very slow operation
        monitor.record_operation("slow_operation", success=True, duration_seconds=150)
        
        # Should have triggered a slow operation alert
        slow_alerts = [a for a in alert_calls if "Slow Operation" in a.title]
        assert len(slow_alerts) == 1
        
        alert = slow_alerts[0]
        assert alert.level == AlertLevel.WARNING
        assert "150" in alert.message
    
    def test_browser_event_recording(self):
        """Test browser event recording."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        monitor = ApplicationMonitor(metrics, alerts)
        
        monitor.record_browser_event("page_load", success=True)
        monitor.record_browser_event("click_button", success=False, context={"button_id": "submit"})
        
        # Check metrics were recorded
        browser_metrics = metrics.get_metrics("browser.event.count")
        assert len(browser_metrics) == 2
        
        # Check tags
        success_metric = [m for m in browser_metrics if m.tags["success"] == "True"][0]
        failure_metric = [m for m in browser_metrics if m.tags["success"] == "False"][0]
        
        assert success_metric.tags["event_type"] == "page_load"
        assert failure_metric.tags["event_type"] == "click_button"
    
    def test_get_health_metrics(self):
        """Test health metrics calculation."""
        metrics = MetricsCollector()
        alerts = AlertManager()
        monitor = ApplicationMonitor(metrics, alerts)
        
        # Record some operations
        for _ in range(7):
            monitor.record_operation("test_op", success=True, duration_seconds=1.0)
        for _ in range(3):
            monitor.record_operation("test_op", success=False, duration_seconds=0.5)
        
        health_metrics = monitor.get_health_metrics()
        
        assert health_metrics["total_operations"] == 10
        assert health_metrics["success_rate"] == 0.7
        assert health_metrics["error_rate"] == 0.3
        assert health_metrics["average_response_time_seconds"] == 0.85  # (7*1.0 + 3*0.5) / 10

# Integration tests
class TestMonitoringIntegration:
    """Integration tests for the complete monitoring system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring(self):
        """Test complete monitoring workflow."""
        # Setup components
        metrics = MetricsCollector()
        alerts = AlertManager()
        health_checker = HealthChecker()
        app_monitor = ApplicationMonitor(metrics, alerts)
        
        alert_calls = []
        def capture_alerts(alert):
            alert_calls.append(alert)
        alerts.add_alert_handler(capture_alerts)
        
        # Add a health check
        def sample_health_check():
            return HealthCheck(
                name="sample",
                status=HealthStatus.HEALTHY,
                message="OK",
                duration_ms=0,
                timestamp=datetime.now(timezone.utc)
            )
        health_checker.register_check("sample", sample_health_check)
        
        # Simulate some application activity
        app_monitor.record_operation("reservation", success=True, duration_seconds=45.0)
        app_monitor.record_operation("verification", success=True, duration_seconds=10.0)
        app_monitor.record_browser_event("navigation", success=True)
        
        # Run health checks
        health_results = await health_checker.run_all_checks()
        
        # Verify everything is working
        assert len(health_results) == 1
        assert health_results["sample"].status == HealthStatus.HEALTHY
        
        # Check metrics were collected
        operation_metrics = metrics.get_metrics("app.operation.count")
        browser_metrics = metrics.get_metrics("browser.event.count")
        
        assert len(operation_metrics) == 2
        assert len(browser_metrics) == 1
        
        # Verify health metrics
        health_metrics = app_monitor.get_health_metrics()
        assert health_metrics["total_operations"] == 2
        assert health_metrics["success_rate"] == 1.0
        assert health_metrics["error_rate"] == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])