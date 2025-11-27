"""
Health Checker
Performs automated health checks on data systems
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import psycopg2
import requests
from sqlalchemy import create_engine, text

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}

class HealthChecker:
    """Performs health checks on various systems"""
    
    def __init__(self):
        self.results: List[HealthCheckResult] = []
    
    def check_database(self, connection_string: str, 
                      timeout: int = 5) -> HealthCheckResult:
        """Check database connectivity and health"""
        try:
            engine = create_engine(connection_string, connect_args={
                'connect_timeout': timeout
            })
            
            with engine.connect() as conn:
                # Simple query to test connectivity
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Check connection pool
                pool = engine.pool
                pool_status = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow()
                }
                
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    details=pool_status
                )
        
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )
    
    def check_api(self, url: str, timeout: int = 5,
                 expected_status: int = 200) -> HealthCheckResult:
        """Check API endpoint health"""
        try:
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == expected_status:
                return HealthCheckResult(
                    name="api",
                    status=HealthStatus.HEALTHY,
                    message=f"API responded with status {response.status_code}",
                    details={
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                )
            else:
                return HealthCheckResult(
                    name="api",
                    status=HealthStatus.DEGRADED,
                    message=f"API returned unexpected status {response.status_code}",
                    details={'status_code': response.status_code}
                )
        
        except requests.Timeout:
            return HealthCheckResult(
                name="api",
                status=HealthStatus.UNHEALTHY,
                message="API request timed out"
            )
        except Exception as e:
            return HealthCheckResult(
                name="api",
                status=HealthStatus.UNHEALTHY,
                message=f"API check failed: {str(e)}"
            )
    
    def check_pipeline_freshness(self, last_run_time: datetime,
                                 expected_interval: timedelta) -> HealthCheckResult:
        """Check if pipeline is running on schedule"""
        now = datetime.now()
        time_since_last_run = now - last_run_time
        
        if time_since_last_run <= expected_interval:
            return HealthCheckResult(
                name="pipeline_freshness",
                status=HealthStatus.HEALTHY,
                message="Pipeline is running on schedule",
                details={
                    'last_run': last_run_time.isoformat(),
                    'time_since_last_run_minutes': time_since_last_run.total_seconds() / 60
                }
            )
        elif time_since_last_run <= expected_interval * 2:
            return HealthCheckResult(
                name="pipeline_freshness",
                status=HealthStatus.DEGRADED,
                message="Pipeline is delayed",
                details={
                    'last_run': last_run_time.isoformat(),
                    'delay_minutes': (time_since_last_run - expected_interval).total_seconds() / 60
                }
            )
        else:
            return HealthCheckResult(
                name="pipeline_freshness",
                status=HealthStatus.UNHEALTHY,
                message="Pipeline is significantly delayed",
                details={
                    'last_run': last_run_time.isoformat(),
                    'delay_minutes': (time_since_last_run - expected_interval).total_seconds() / 60
                }
            )
    
    def check_disk_space(self, path: str, threshold_percent: float = 10.0) -> HealthCheckResult:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            free_percent = (free / total) * 100
            
            if free_percent >= threshold_percent:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space available ({free_percent:.1f}%)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Low disk space ({free_percent:.1f}% free)"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    'total_gb': total / (1024**3),
                    'used_gb': used / (1024**3),
                    'free_gb': free / (1024**3),
                    'free_percent': free_percent
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check disk space: {str(e)}"
            )
    
    def run_all_checks(self, checks: List[callable]) -> List[HealthCheckResult]:
        """Run multiple health checks"""
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(HealthCheckResult(
                    name="unknown",
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {str(e)}"
                ))
        
        self.results.extend(results)
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall health status from all checks"""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self.results]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

