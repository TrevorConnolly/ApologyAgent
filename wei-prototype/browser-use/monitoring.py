"""
Monitoring and observability utilities for the Restaurant Kernel Agent.
Provides structured logging, metrics collection, health checks, and alerting.
"""

import os
import logging
import time
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import psutil
import hashlib

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        if hasattr(record, 'performance_metric'):
            log_entry['performance_metric'] = record.performance_metric
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Structured alert information."""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    source: str = "restaurant-agent"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

@dataclass
class Metric:
    """Structured metric information."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class MetricsCollector:
    """Collect and aggregate application metrics."""
    
    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics = defaultdict(lambda: deque(maxlen=retention_minutes * 60))  # 1 per second max
        self._lock = threading.Lock()
        
    def record_metric(self, metric: Metric):
        """Record a metric value."""
        with self._lock:
            metric_key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in sorted(metric.tags.items()))}"
            self.metrics[metric_key].append(metric)
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = None):
        """Record a metric with simplified interface."""
        metric = Metric(name=name, value=value, tags=tags or {}, unit=unit, 
                       timestamp=datetime.now(timezone.utc))
        self.record_metric(metric)
    
    def get_metrics(self, name: str = None, since_minutes: int = 5) -> List[Metric]:
        """Get metrics, optionally filtered by name and time."""
        since_time = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
        
        with self._lock:
            if name:
                # Filter by specific metric name
                result = []
                for key, metrics in self.metrics.items():
                    if key.startswith(f"{name}:"):
                        result.extend([m for m in metrics if m.timestamp.timestamp() >= since_time])
                return result
            else:
                # Return all recent metrics
                result = []
                for metrics in self.metrics.values():
                    result.extend([m for m in metrics if m.timestamp.timestamp() >= since_time])
                return result
    
    def get_summary(self, name: str, since_minutes: int = 5) -> Dict[str, float]:
        """Get summary statistics for a metric."""
        metrics = self.get_metrics(name, since_minutes)
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'sum': sum(values),
            'latest': values[-1] if values else 0
        }

class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)  # Keep last 1000 alerts
        self.alert_handlers = []
        self._lock = threading.Lock()
        
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add a handler for processing alerts."""
        self.alert_handlers.append(handler)
    
    def send_alert(self, alert: Alert):
        """Send an alert through all configured handlers."""
        with self._lock:
            self.alerts.append(alert)
            
        # Process through handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logging.error(f"Alert handler failed: {e}")
    
    def alert(self, level: AlertLevel, title: str, message: str, 
             context: Dict[str, Any] = None, tags: List[str] = None):
        """Send an alert with simplified interface."""
        alert = Alert(
            level=level,
            title=title,
            message=message,
            context=context or {},
            tags=tags or [],
            timestamp=datetime.now(timezone.utc)
        )
        self.send_alert(alert)
    
    def get_alerts(self, level: AlertLevel = None, since_minutes: int = 60) -> List[Alert]:
        """Get recent alerts, optionally filtered by level."""
        since_time = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
        
        with self._lock:
            alerts = [a for a in self.alerts if a.timestamp.timestamp() >= since_time]
            if level:
                alerts = [a for a in alerts if a.level == level]
            return alerts

class HealthChecker:
    """Perform system health checks."""
    
    def __init__(self):
        self.checks = {}
        self.last_results = {}
        
    def register_check(self, name: str, check_func: Callable[[], HealthCheck]):
        """Register a health check function."""
        self.checks[name] = check_func
    
    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Unknown health check: {name}",
                duration_ms=0,
                timestamp=datetime.now(timezone.utc)
            )
        
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(self.checks[name]):
                result = await self.checks[name]()
            else:
                result = self.checks[name]()
            
            result.duration_ms = (time.time() - start_time) * 1000
            self.last_results[name] = result
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
                details={'exception': str(e)}
            )
            self.last_results[name] = result
            return result
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        results = {}
        for name in self.checks:
            results[name] = await self.run_check(name)
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.last_results:
            return HealthStatus.UNHEALTHY
        
        statuses = [result.status for result in self.last_results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

class SystemMonitor:
    """Monitor system resources and performance."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self._monitoring = False
        self._monitor_task = None
        
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous system monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self, interval_seconds: int):
        """Continuous monitoring loop."""
        while self._monitoring:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"System monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def collect_system_metrics(self):
        """Collect current system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.record('system.cpu.usage_percent', cpu_percent, tags={'type': 'overall'})
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics.record('system.memory.usage_percent', memory.percent, tags={'type': 'virtual'})
        self.metrics.record('system.memory.available_bytes', memory.available, tags={'type': 'virtual'})
        self.metrics.record('system.memory.used_bytes', memory.used, tags={'type': 'virtual'})
        
        # Process-specific metrics
        process = psutil.Process()
        proc_memory = process.memory_info()
        self.metrics.record('process.memory.rss_bytes', proc_memory.rss, tags={'type': 'resident'})
        self.metrics.record('process.memory.vms_bytes', proc_memory.vms, tags={'type': 'virtual'})
        
        proc_cpu = process.cpu_percent()
        self.metrics.record('process.cpu.usage_percent', proc_cpu, tags={'type': 'process'})
        
        # Disk metrics
        disk_usage = psutil.disk_usage('/')
        self.metrics.record('system.disk.usage_percent', 
                          (disk_usage.used / disk_usage.total) * 100, 
                          tags={'mount': '/'})
        
        # Network metrics (if available)
        try:
            net_io = psutil.net_io_counters()
            self.metrics.record('system.network.bytes_sent', net_io.bytes_sent)
            self.metrics.record('system.network.bytes_recv', net_io.bytes_recv)
        except:
            pass  # Network metrics not available on all systems

class ApplicationMonitor:
    """Monitor application-specific metrics and events."""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics = metrics_collector
        self.alerts = alert_manager
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        
    def record_operation(self, operation: str, success: bool = True, 
                        duration_seconds: float = None, context: Dict = None):
        """Record an application operation."""
        tags = {'operation': operation, 'success': str(success)}
        
        # Count operations
        self.operation_counts[f"{operation}:{'success' if success else 'error'}"] += 1
        self.metrics.record('app.operation.count', 1, tags=tags)
        
        # Record response time
        if duration_seconds is not None:
            self.metrics.record('app.operation.duration_seconds', duration_seconds, tags=tags)
            self.response_times[operation].append(duration_seconds)
            
            # Alert on slow operations
            if duration_seconds > 120:  # 2 minutes
                self.alerts.alert(
                    AlertLevel.WARNING,
                    f"Slow Operation: {operation}",
                    f"Operation took {duration_seconds:.2f} seconds",
                    context={'operation': operation, 'duration': duration_seconds, **(context or {})}
                )
        
        # Track error rates
        if not success:
            self.error_counts[operation] += 1
            
            # Check error rate
            total_ops = self.operation_counts.get(f"{operation}:success", 0) + self.operation_counts.get(f"{operation}:error", 0)
            if total_ops >= 10:  # Only alert after sufficient operations
                error_rate = self.error_counts[operation] / total_ops
                if error_rate > 0.1:  # 10% error rate
                    self.alerts.alert(
                        AlertLevel.ERROR,
                        f"High Error Rate: {operation}",
                        f"Error rate is {error_rate:.1%} for {operation}",
                        context={'operation': operation, 'error_rate': error_rate, 'total_operations': total_ops}
                    )
    
    def record_browser_event(self, event_type: str, success: bool = True, context: Dict = None):
        """Record browser-specific events."""
        tags = {'event_type': event_type, 'success': str(success)}
        self.metrics.record('browser.event.count', 1, tags=tags)
        
        if not success and context:
            self.alerts.alert(
                AlertLevel.WARNING,
                f"Browser Event Failed: {event_type}",
                f"Browser event {event_type} failed",
                context=context,
                tags=['browser', event_type]
            )
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get application health metrics."""
        # Calculate overall success rate
        total_success = sum(count for op, count in self.operation_counts.items() if op.endswith(':success'))
        total_error = sum(count for op, count in self.operation_counts.items() if op.endswith(':error'))
        total_ops = total_success + total_error
        
        success_rate = (total_success / total_ops) if total_ops > 0 else 1.0
        
        # Calculate average response time
        all_response_times = []
        for times in self.response_times.values():
            all_response_times.extend(times)
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        return {
            'total_operations': total_ops,
            'success_rate': success_rate,
            'error_rate': 1 - success_rate,
            'average_response_time_seconds': avg_response_time,
            'recent_operations': dict(self.operation_counts),
            'recent_errors': dict(self.error_counts)
        }

# Webhook alert handlers
async def slack_webhook_handler(alert: Alert):
    """Send alert to Slack webhook."""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    color_map = {
        AlertLevel.INFO: 'good',
        AlertLevel.WARNING: 'warning',
        AlertLevel.ERROR: 'danger',
        AlertLevel.CRITICAL: 'danger'
    }
    
    payload = {
        'text': f"🤖 Restaurant Agent Alert: {alert.title}",
        'attachments': [{
            'color': color_map.get(alert.level, 'warning'),
            'title': alert.title,
            'text': alert.message,
            'fields': [
                {'title': 'Level', 'value': alert.level.value.upper(), 'short': True},
                {'title': 'Source', 'value': alert.source, 'short': True},
                {'title': 'Time', 'value': alert.timestamp.isoformat(), 'short': True}
            ]
        }]
    }
    
    if alert.context:
        payload['attachments'][0]['fields'].append({
            'title': 'Context',
            'value': json.dumps(alert.context, indent=2),
            'short': False
        })
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send Slack alert: {e}")

# Global monitoring instances
metrics_collector = MetricsCollector()
alert_manager = AlertManager()
health_checker = HealthChecker()
system_monitor = SystemMonitor(metrics_collector)
app_monitor = ApplicationMonitor(metrics_collector, alert_manager)

# Configure structured logging
def setup_logging(log_level: str = "INFO", use_json: bool = True):
    """Configure structured logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create new handler
    handler = logging.StreamHandler()
    
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Also log to file if specified
    log_file = os.getenv('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger