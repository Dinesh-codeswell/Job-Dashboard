"""
ADVANCED SCRAPER ENGINE
=======================
Production-grade optimizations for performance, reliability, and security.

Features:
- Connection pooling & caching
- Circuit breaker pattern
- Fuzzy duplicate detection
- Advanced rate limiting
- Performance profiling
- Memory optimization
"""

import asyncio
import hashlib
import logging
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
import difflib
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 300  # Seconds before half-open
    success_threshold: int = 2   # Successes to close


@dataclass
class RateLimitConfig:
    """Rate limit configuration per platform."""
    calls_per_hour: int = 200
    calls_per_minute: int = 20
    min_delay_seconds: float = 0.5


@dataclass
class PerformanceMetrics:
    """Performance metrics for tracking."""
    platform: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    jobs_attempted: int = 0
    jobs_successful: int = 0
    jobs_failed: int = 0
    jobs_filtered: int = 0
    jobs_duplicate: int = 0
    errors_temporary: int = 0
    errors_permanent: int = 0
    retries_total: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def duration(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.jobs_attempted == 0:
            return 0.0
        return (self.jobs_successful / self.jobs_attempted) * 100
    
    def jobs_per_second(self) -> float:
        """Get jobs per second."""
        duration = self.duration()
        if duration == 0:
            return 0.0
        return self.jobs_successful / duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform": self.platform,
            "duration_seconds": round(self.duration(), 2),
            "jobs_attempted": self.jobs_attempted,
            "jobs_successful": self.jobs_successful,
            "jobs_failed": self.jobs_failed,
            "jobs_filtered": self.jobs_filtered,
            "jobs_duplicate": self.jobs_duplicate,
            "errors_temporary": self.errors_temporary,
            "errors_permanent": self.errors_permanent,
            "retries_total": self.retries_total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "success_rate": round(self.success_rate(), 2),
            "jobs_per_second": round(self.jobs_per_second(), 2),
        }


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' re-opened after failure")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPEN after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has passed."""
        if not self.last_failure_time:
            return False
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
            }


# ============================================================================
# ADVANCED RATE LIMITER
# ============================================================================

class AdvancedRateLimiter:
    """
    Token bucket rate limiter with per-platform configuration.
    Supports both per-hour and per-minute limits.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.configs: Dict[str, RateLimitConfig] = {
            "linkedin": RateLimitConfig(calls_per_hour=200, calls_per_minute=20),
            "indeed": RateLimitConfig(calls_per_hour=100, calls_per_minute=15),
            "naukri": RateLimitConfig(calls_per_hour=100, calls_per_minute=15),
        }
        self.tokens: Dict[str, float] = defaultdict(float)
        self.last_refill: Dict[str, float] = defaultdict(time.time)
        self.lock = threading.Lock()
    
    async def acquire(self, platform: str, tokens: int = 1) -> float:
        """
        Acquire tokens from rate limiter.
        Returns wait time in seconds.
        """
        config = self.configs.get(platform)
        if not config:
            return 0.0
        
        with self.lock:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_refill[platform]
            
            # Refill at per-minute rate
            refill_rate = config.calls_per_minute / 60.0
            self.tokens[platform] += elapsed * refill_rate
            
            # Cap at hourly limit
            max_tokens = config.calls_per_hour / 3600.0 * 60.0
            self.tokens[platform] = min(self.tokens[platform], max_tokens)
            
            self.last_refill[platform] = now
            
            # Wait if not enough tokens
            if self.tokens[platform] < tokens:
                wait_time = (tokens - self.tokens[platform]) / refill_rate
                logger.debug(f"{platform}: Rate limited, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens[platform] = 0
            else:
                self.tokens[platform] -= tokens
        
        return 0.0
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                platform: {
                    "tokens_available": round(self.tokens[platform], 2),
                    "config": asdict(self.configs[platform]),
                }
                for platform in self.configs
            }


# ============================================================================
# ADVANCED DEDUPLICATOR
# ============================================================================

class AdvancedDeduplicator:
    """
    Multi-level deduplication with fuzzy matching.
    Detects exact duplicates, content-based duplicates, and similar jobs.
    """
    
    def __init__(self, fuzzy_threshold: float = 0.85):
        """Initialize deduplicator."""
        self.fuzzy_threshold = fuzzy_threshold
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Dict[str, str] = {}  # hash -> job_url
        self.job_cache: Dict[str, Dict[str, Any]] = {}  # url -> job_data
        self.lock = threading.Lock()
    
    def compute_content_hash(self, job_data: Dict[str, Any]) -> str:
        """Compute SHA256 hash of job content."""
        content = f"{job_data.get('job_title', '')}|{job_data.get('company', '')}|{job_data.get('location', '')}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def compute_fuzzy_signature(self, job_data: Dict[str, Any]) -> str:
        """Compute fuzzy signature for similarity matching."""
        title = job_data.get('job_title', '').lower().strip()
        company = job_data.get('company', '').lower().strip()
        # Remove common words and normalize
        title = ' '.join(w for w in title.split() if len(w) > 3)
        return f"{title}|{company}"
    
    def is_duplicate(self, job_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if job is duplicate using multi-level detection.
        Returns (is_duplicate, reason).
        """
        with self.lock:
            job_url = job_data.get('job_url', '')
            
            # Level 1: URL-based (exact match)
            if job_url in self.seen_urls:
                return True, "URL already seen"
            
            # Level 2: Content-based (SHA256 hash)
            content_hash = self.compute_content_hash(job_data)
            if content_hash in self.seen_hashes:
                return True, f"Content hash match with {self.seen_hashes[content_hash]}"
            
            # Level 3: Fuzzy matching (similarity)
            fuzzy_sig = self.compute_fuzzy_signature(job_data)
            for existing_url, existing_data in self.job_cache.items():
                existing_sig = self.compute_fuzzy_signature(existing_data)
                similarity = difflib.SequenceMatcher(None, fuzzy_sig, existing_sig).ratio()
                if similarity >= self.fuzzy_threshold:
                    return True, f"Fuzzy match ({similarity:.2%}) with {existing_url}"
            
            return False, "Not a duplicate"
    
    def mark_as_seen(self, job_data: Dict[str, Any]):
        """Mark job as seen."""
        with self.lock:
            job_url = job_data.get('job_url', '')
            content_hash = self.compute_content_hash(job_data)
            
            self.seen_urls.add(job_url)
            self.seen_hashes[content_hash] = job_url
            self.job_cache[job_url] = job_data
    
    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        with self.lock:
            return {
                "unique_urls": len(self.seen_urls),
                "unique_hashes": len(self.seen_hashes),
                "cache_size": len(self.job_cache),
            }
    
    def clear_old_cache(self, max_age_hours: int = 24):
        """Clear cache entries older than max_age_hours."""
        with self.lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=max_age_hours)
            
            to_remove = []
            for url, job_data in self.job_cache.items():
                scraped_at = job_data.get('scraped_at', '')
                if scraped_at:
                    try:
                        job_time = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                        if job_time < cutoff:
                            to_remove.append(url)
                    except:
                        pass
            
            for url in to_remove:
                del self.job_cache[url]
                self.seen_urls.discard(url)
            
            logger.info(f"Cleared {len(to_remove)} old cache entries")


# ============================================================================
# PERFORMANCE PROFILER
# ============================================================================

class PerformanceProfiler:
    """
    Detailed performance profiling and analysis.
    Tracks metrics by platform and operation type.
    """
    
    def __init__(self):
        """Initialize profiler."""
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def get_metrics(self, platform: str) -> PerformanceMetrics:
        """Get or create metrics for platform."""
        with self.lock:
            if platform not in self.metrics:
                self.metrics[platform] = PerformanceMetrics(platform=platform)
            return self.metrics[platform]
    
    def record_operation(self, operation: str, duration: float):
        """Record operation duration."""
        with self.lock:
            self.operation_times[operation].append(duration)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for operation."""
        with self.lock:
            times = self.operation_times.get(operation, [])
            if not times:
                return {}
            
            times_sorted = sorted(times)
            return {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "p50": times_sorted[len(times) // 2],
                "p95": times_sorted[int(len(times) * 0.95)],
                "p99": times_sorted[int(len(times) * 0.99)],
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete performance summary."""
        with self.lock:
            total_jobs = sum(m.jobs_successful for m in self.metrics.values())
            total_duration = max(
                (m.duration() for m in self.metrics.values()),
                default=0
            )
            
            return {
                "total_jobs": total_jobs,
                "total_duration_seconds": round(total_duration, 2),
                "jobs_per_second": round(total_jobs / total_duration, 2) if total_duration > 0 else 0,
                "by_platform": {
                    name: metrics.to_dict()
                    for name, metrics in self.metrics.items()
                },
                "operations": {
                    op: self.get_operation_stats(op)
                    for op in self.operation_times.keys()
                }
            }


# ============================================================================
# MEMORY OPTIMIZER
# ============================================================================

class MemoryOptimizer:
    """
    Memory optimization and monitoring.
    Implements LRU cache and memory limits.
    """
    
    def __init__(self, max_cache_size: int = 10000):
        """Initialize memory optimizer."""
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache with LRU eviction."""
        with self.lock:
            # Evict LRU item if cache is full
            if len(self.cache) >= self.max_cache_size:
                lru_key = min(self.access_times, key=self.access_times.get)
                del self.cache[lru_key]
                del self.access_times[lru_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with self.lock:
            return {
                "cache_size": len(self.cache),
                "max_cache_size": self.max_cache_size,
                "cache_utilization": f"{(len(self.cache) / self.max_cache_size * 100):.1f}%",
            }


# ============================================================================
# INTEGRATED ADVANCED ENGINE
# ============================================================================

class AdvancedScraperEngine:
    """
    Integrated advanced scraper engine with all optimizations.
    """
    
    def __init__(self):
        """Initialize advanced engine."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "linkedin": CircuitBreaker("linkedin", CircuitBreakerConfig()),
            "indeed": CircuitBreaker("indeed", CircuitBreakerConfig()),
            "naukri": CircuitBreaker("naukri", CircuitBreakerConfig()),
        }
        self.rate_limiter = AdvancedRateLimiter()
        self.deduplicator = AdvancedDeduplicator()
        self.profiler = PerformanceProfiler()
        self.memory_optimizer = MemoryOptimizer()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        return {
            "circuit_breakers": {
                name: cb.get_state()
                for name, cb in self.circuit_breakers.items()
            },
            "rate_limits": self.rate_limiter.get_stats(),
            "deduplication": self.deduplicator.get_stats(),
            "memory": self.memory_optimizer.get_stats(),
            "performance": self.profiler.get_summary(),
        }
    
    def save_health_report(self, filepath: str = "health_report.json"):
        """Save health report to file."""
        report = self.get_health_status()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Health report saved to {filepath}")
