"""
Performance Regression Detection - Automated Performance Monitoring
===================================================================

Implements Claude Online's recommendation for performance regression detection:
- Baseline performance tracking across test runs
- Automated regression alerts with configurable thresholds
- Performance trend analysis and reporting
- Integration with bulletproof testing framework
"""

import json
import time
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass 
class PerformanceBaseline:
    """Performance baseline for a specific test or operation."""
    test_name: str
    operation: str
    baseline_duration: float
    sample_count: int
    last_updated: float
    min_duration: float
    max_duration: float
    std_deviation: float


@dataclass
class PerformanceResult:
    """Performance test result."""
    test_name: str
    operation: str
    duration: float
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class RegressionAlert:
    """Performance regression alert."""
    test_name: str
    operation: str
    current_duration: float
    baseline_duration: float
    regression_percent: float
    severity: str  # 'minor', 'major', 'critical'
    timestamp: float


class PerformanceRegressionDetector:
    """Automated performance regression detection and alerting."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.baselines_file = self.project_root / "testing" / "performance" / "baselines.json"
        self.results_dir = self.project_root / "testing" / "performance" / "results"
        
        # Regression thresholds
        self.MINOR_THRESHOLD = 15      # 15% slower = minor regression
        self.MAJOR_THRESHOLD = 30      # 30% slower = major regression  
        self.CRITICAL_THRESHOLD = 50   # 50% slower = critical regression
        
        # Minimum samples for reliable baselines
        self.MIN_SAMPLES = 5
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories."""
        self.baselines_file.parent.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def record_performance(self, test_name: str, operation: str, duration: float,
                          metadata: Dict[str, Any] = None) -> bool:
        """
        Record performance result and check for regressions.
        
        Args:
            test_name: Name of the test (e.g., "test_websocket_connection")
            operation: Specific operation (e.g., "connection_time", "message_latency")
            duration: Duration in seconds
            metadata: Additional context (test environment, data size, etc.)
        
        Returns:
            bool: True if no regression detected, False if regression found
        """
        result = PerformanceResult(
            test_name=test_name,
            operation=operation,
            duration=duration,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Store result
        self._store_result(result)
        
        # Check for regression
        regression = self._check_regression(result)
        
        if regression:
            self._handle_regression(regression)
            return False
        
        # Update baseline if appropriate
        self._update_baseline(result)
        return True
    
    def get_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Load current performance baselines."""
        if not self.baselines_file.exists():
            return {}
        
        try:
            with open(self.baselines_file, 'r') as f:
                baselines_data = json.load(f)
            
            baselines = {}
            for key, data in baselines_data.items():
                baselines[key] = PerformanceBaseline(**data)
            
            return baselines
        except Exception as e:
            print(f"Warning: Could not load baselines: {e}")
            return {}
    
    def _store_result(self, result: PerformanceResult):
        """Store performance result for trend analysis."""
        date_str = datetime.fromtimestamp(result.timestamp).strftime("%Y-%m-%d")
        results_file = self.results_dir / f"performance_{date_str}.json"
        
        # Load existing results
        results = []
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
            except Exception:
                results = []
        
        # Add new result
        results.append(asdict(result))
        
        # Save updated results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def _check_regression(self, result: PerformanceResult) -> Optional[RegressionAlert]:
        """Check if result indicates performance regression."""
        baselines = self.get_baselines()
        baseline_key = f"{result.test_name}:{result.operation}"
        
        baseline = baselines.get(baseline_key)
        if not baseline:
            return None  # No baseline to compare against
        
        # Calculate regression percentage
        regression_percent = ((result.duration - baseline.baseline_duration) 
                            / baseline.baseline_duration) * 100
        
        # Determine severity
        severity = None
        if regression_percent >= self.CRITICAL_THRESHOLD:
            severity = "critical"
        elif regression_percent >= self.MAJOR_THRESHOLD:
            severity = "major"
        elif regression_percent >= self.MINOR_THRESHOLD:
            severity = "minor"
        
        if severity:
            return RegressionAlert(
                test_name=result.test_name,
                operation=result.operation,
                current_duration=result.duration,
                baseline_duration=baseline.baseline_duration,
                regression_percent=regression_percent,
                severity=severity,
                timestamp=result.timestamp
            )
        
        return None
    
    def _handle_regression(self, regression: RegressionAlert):
        """Handle detected performance regression."""
        # Log regression
        print(f"🚨 Performance Regression Detected!")
        print(f"   Test: {regression.test_name}")
        print(f"   Operation: {regression.operation}")
        print(f"   Current: {regression.current_duration:.3f}s")
        print(f"   Baseline: {regression.baseline_duration:.3f}s")
        print(f"   Regression: {regression.regression_percent:.1f}% slower")
        print(f"   Severity: {regression.severity.upper()}")
        
        # Store regression alert
        alerts_file = self.results_dir / "regression_alerts.json"
        alerts = []
        
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        
        alerts.append(asdict(regression))
        
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        # Additional actions based on severity
        if regression.severity == "critical":
            print(f"   🔥 CRITICAL: Consider investigating immediately!")
        elif regression.severity == "major":
            print(f"   ⚠️  MAJOR: Investigate before next release")
        else:
            print(f"   ℹ️  MINOR: Monitor trend")
    
    def _update_baseline(self, result: PerformanceResult):
        """Update baseline with new result if appropriate."""
        baselines = self.get_baselines()
        baseline_key = f"{result.test_name}:{result.operation}"
        
        # Get recent results for this test/operation
        recent_results = self._get_recent_results(result.test_name, result.operation, days=7)
        
        if len(recent_results) < self.MIN_SAMPLES:
            return  # Not enough samples for reliable baseline
        
        # Calculate new baseline statistics
        durations = [r.duration for r in recent_results]
        
        new_baseline = PerformanceBaseline(
            test_name=result.test_name,
            operation=result.operation,
            baseline_duration=statistics.median(durations),  # Use median for robustness
            sample_count=len(durations),
            last_updated=time.time(),
            min_duration=min(durations),
            max_duration=max(durations),
            std_deviation=statistics.stdev(durations) if len(durations) > 1 else 0.0
        )
        
        # Update baselines
        baselines[baseline_key] = new_baseline
        
        # Save updated baselines
        self._save_baselines(baselines)
    
    def _get_recent_results(self, test_name: str, operation: str, days: int = 7) -> List[PerformanceResult]:
        """Get recent results for a specific test/operation."""
        cutoff_time = time.time() - (days * 24 * 3600)
        results = []
        
        # Check recent result files
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            results_file = self.results_dir / f"performance_{date_str}.json"
            
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        daily_results = json.load(f)
                    
                    for result_data in daily_results:
                        if (result_data['test_name'] == test_name and 
                            result_data['operation'] == operation and
                            result_data['timestamp'] >= cutoff_time):
                            
                            results.append(PerformanceResult(**result_data))
                            
                except Exception:
                    continue
        
        return sorted(results, key=lambda r: r.timestamp)
    
    def _save_baselines(self, baselines: Dict[str, PerformanceBaseline]):
        """Save performance baselines to file."""
        baselines_data = {key: asdict(baseline) for key, baseline in baselines.items()}
        
        with open(self.baselines_file, 'w') as f:
            json.dump(baselines_data, f, indent=2)
    
    def generate_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        baselines = self.get_baselines()
        
        # Get all results from specified period
        cutoff_time = time.time() - (days * 24 * 3600)
        all_results = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            results_file = self.results_dir / f"performance_{date_str}.json"
            
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        daily_results = json.load(f)
                    
                    for result_data in daily_results:
                        if result_data['timestamp'] >= cutoff_time:
                            all_results.append(PerformanceResult(**result_data))
                except Exception:
                    continue
        
        # Calculate trends
        trends = {}
        for result in all_results:
            key = f"{result.test_name}:{result.operation}"
            if key not in trends:
                trends[key] = []
            trends[key].append(result.duration)
        
        # Load regression alerts
        alerts_file = self.results_dir / "regression_alerts.json"
        recent_alerts = []
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                
                for alert_data in alerts_data:
                    if alert_data['timestamp'] >= cutoff_time:
                        recent_alerts.append(RegressionAlert(**alert_data))
            except Exception:
                pass
        
        return {
            "report_period_days": days,
            "total_tests": len(set(r.test_name for r in all_results)),
            "total_measurements": len(all_results),
            "baselines_count": len(baselines),
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a.severity == "critical"]),
            "major_alerts": len([a for a in recent_alerts if a.severity == "major"]),
            "minor_alerts": len([a for a in recent_alerts if a.severity == "minor"]),
            "trends": {key: {
                "samples": len(durations),
                "avg_duration": statistics.mean(durations),
                "trend": self._calculate_trend(durations)
            } for key, durations in trends.items() if len(durations) > 1},
            "generated_at": time.time()
        }
    
    def _calculate_trend(self, durations: List[float]) -> str:
        """Calculate performance trend (improving, stable, degrading)."""
        if len(durations) < 3:
            return "insufficient_data"
        
        # Simple trend calculation: compare first third to last third
        first_third = durations[:len(durations)//3]
        last_third = durations[-len(durations)//3:]
        
        first_avg = statistics.mean(first_third)
        last_avg = statistics.mean(last_third)
        
        change_percent = ((last_avg - first_avg) / first_avg) * 100
        
        if change_percent < -5:
            return "improving"
        elif change_percent > 5:
            return "degrading"  
        else:
            return "stable"


# Usage example with bulletproof testing framework integration
class PerformanceTestMixin:
    """Mixin for adding performance monitoring to tests."""
    
    def __init__(self):
        self.perf_detector = PerformanceRegressionDetector()
    
    def measure_performance(self, operation: str, func, *args, **kwargs):
        """Decorator/context manager for measuring test performance."""
        test_name = self.__class__.__name__
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record performance
            self.perf_detector.record_performance(
                test_name=test_name,
                operation=operation,
                duration=duration,
                metadata={
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed performance (for timeout analysis)
            self.perf_detector.record_performance(
                test_name=test_name,
                operation=f"{operation}_failed",
                duration=duration,
                metadata={
                    "error": str(e),
                    "success": False
                }
            )
            
            raise


# Global instance for easy access
performance_detector = PerformanceRegressionDetector()