"""
OPTIMIZED SCRAPING ENGINE
=========================
Production-ready scraper with:
- Async/concurrent processing
- Retry logic with exponential backoff
- Content-based deduplication
- Rate limiting per platform
- Error recovery
- Performance monitoring
"""

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONTENT DEDUPLICATION
# ============================================================================

class ContentDeduplicator:
    """
    Advanced deduplication using content hashing.
    Detects duplicate jobs even with different URLs.
    """
    
    def __init__(self):
        self.url_hashes: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.title_company_hashes: Set[str] = set()
    
    def compute_content_hash(self, job_data: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of job content.
        Uses title + company + first 500 chars of description.
        """
        title = str(job_data.get('job_title', '')).lower().strip()
        company = str(job_data.get('company', '')).lower().strip()
        description = str(job_data.get('job_description', ''))[:500].lower().strip()
        
        content = f"{title}|{company}|{description}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def compute_title_company_hash(self, job_data: Dict[str, Any]) -> str:
        """
        Compute hash of title + company only.
        Faster check for obvious duplicates.
        """
        title = str(job_data.get('job_title', '')).lower().strip()
        company = str(job_data.get('company', '')).lower().strip()
        
        content = f"{title}|{company}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, job_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if job is duplicate using multiple strategies.
        
        Returns:
            (is_duplicate, reason)
        """
        job_url = job_data.get('job_url', '')
        
        # Strategy 1: URL check (fastest)
        if job_url and job_url in self.url_hashes:
            return True, "duplicate_url"
        
        # Strategy 2: Title + Company check (fast)
        tc_hash = self.compute_title_company_hash(job_data)
        if tc_hash in self.title_company_hashes:
            return True, "duplicate_title_company"
        
        # Strategy 3: Content hash check (thorough)
        content_hash = self.compute_content_hash(job_data)
        if content_hash in self.content_hashes:
            return True, "duplicate_content"
        
        return False, ""
    
    def mark_as_seen(self, job_data: Dict[str, Any]):
        """Mark job as seen to prevent future duplicates."""
        job_url = job_data.get('job_url', '')
        if job_url:
            self.url_hashes.add(job_url)
        
        tc_hash = self.compute_title_company_hash(job_data)
        self.title_company_hashes.add(tc_hash)
        
        content_hash = self.compute_content_hash(job_data)
        self.content_hashes.add(content_hash)
    
    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return {
            "url_hashes": len(self.url_hashes),
            "title_company_hashes": len(self.title_company_hashes),
            "content_hashes": len(self.content_hashes)
        }


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """
    Adaptive rate limiter per platform.
    Prevents IP bans and respects platform limits.
    """
    
    def __init__(self):
        self.limits = {
            'linkedin': {'calls': 200, 'period': 3600, 'min_delay': 0.5},  # 200/hour, 0.5s between calls
            'indeed': {'calls': 100, 'period': 3600, 'min_delay': 1.0},   # 100/hour, 1s between calls
            'naukri': {'calls': 100, 'period': 3600, 'min_delay': 1.0}    # 100/hour, 1s between calls
        }
        self.call_history: Dict[str, List[float]] = defaultdict(list)
        self.last_call: Dict[str, float] = {}
    
    async def acquire(self, platform: str):
        """
        Acquire permission to make a call.
        Blocks if rate limit would be exceeded.
        """
        platform = platform.lower()
        if platform not in self.limits:
            return
        
        config = self.limits[platform]
        now = time.time()
        
        # Remove old calls outside the time window
        cutoff = now - config['period']
        self.call_history[platform] = [
            t for t in self.call_history[platform] if t > cutoff
        ]
        
        # Check if we've hit the limit
        if len(self.call_history[platform]) >= config['calls']:
            # Wait until oldest call expires
            oldest = self.call_history[platform][0]
            wait_time = (oldest + config['period']) - now
            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached for {platform}. "
                    f"Waiting {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
                now = time.time()
        
        # Enforce minimum delay between calls
        if platform in self.last_call:
            elapsed = now - self.last_call[platform]
            if elapsed < config['min_delay']:
                await asyncio.sleep(config['min_delay'] - elapsed)
                now = time.time()
        
        # Record this call
        self.call_history[platform].append(now)
        self.last_call[platform] = now
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limiting statistics."""
        stats = {}
        now = time.time()
        
        for platform, config in self.limits.items():
            cutoff = now - config['period']
            recent_calls = [
                t for t in self.call_history[platform] if t > cutoff
            ]
            
            stats[platform] = {
                'calls_in_window': len(recent_calls),
                'limit': config['calls'],
                'remaining': config['calls'] - len(recent_calls),
                'window_seconds': config['period']
            }
        
        return stats


# ============================================================================
# RETRY LOGIC
# ============================================================================

class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class TemporaryError(ScrapingError):
    """Temporary error that should be retried."""
    pass


class PermanentError(ScrapingError):
    """Permanent error that should not be retried."""
    pass


def create_retry_decorator(max_attempts: int = 3):
    """
    Create retry decorator with exponential backoff.
    
    Retries: 1s, 2s, 4s, 8s...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TemporaryError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Track scraping performance metrics."""
    
    platform: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    jobs_attempted: int = 0
    jobs_successful: int = 0
    jobs_failed: int = 0
    jobs_duplicate: int = 0
    jobs_filtered: int = 0
    
    errors_temporary: int = 0
    errors_permanent: int = 0
    errors_network: int = 0
    errors_parsing: int = 0
    
    retries_total: int = 0
    
    def mark_complete(self):
        """Mark scraping as complete."""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def jobs_per_second(self) -> float:
        """Get scraping rate."""
        if self.duration == 0:
            return 0
        return self.jobs_successful / self.duration
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.jobs_attempted == 0:
            return 0
        return (self.jobs_successful / self.jobs_attempted) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform': self.platform,
            'duration_seconds': round(self.duration, 2),
            'jobs_attempted': self.jobs_attempted,
            'jobs_successful': self.jobs_successful,
            'jobs_failed': self.jobs_failed,
            'jobs_duplicate': self.jobs_duplicate,
            'jobs_filtered': self.jobs_filtered,
            'jobs_per_second': round(self.jobs_per_second, 2),
            'success_rate': round(self.success_rate, 2),
            'errors': {
                'temporary': self.errors_temporary,
                'permanent': self.errors_permanent,
                'network': self.errors_network,
                'parsing': self.errors_parsing
            },
            'retries_total': self.retries_total
        }


class PerformanceMonitor:
    """Monitor and aggregate performance across all platforms."""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.start_time = time.time()
    
    def get_metrics(self, platform: str) -> PerformanceMetrics:
        """Get or create metrics for platform."""
        if platform not in self.metrics:
            self.metrics[platform] = PerformanceMetrics(platform=platform)
        return self.metrics[platform]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get aggregated summary."""
        total_duration = time.time() - self.start_time
        
        total_attempted = sum(m.jobs_attempted for m in self.metrics.values())
        total_successful = sum(m.jobs_successful for m in self.metrics.values())
        total_failed = sum(m.jobs_failed for m in self.metrics.values())
        total_duplicate = sum(m.jobs_duplicate for m in self.metrics.values())
        total_filtered = sum(m.jobs_filtered for m in self.metrics.values())
        
        return {
            'total_duration_seconds': round(total_duration, 2),
            'platforms': len(self.metrics),
            'jobs': {
                'attempted': total_attempted,
                'successful': total_successful,
                'failed': total_failed,
                'duplicate': total_duplicate,
                'filtered': total_filtered
            },
            'overall_success_rate': round(
                (total_successful / total_attempted * 100) if total_attempted > 0 else 0,
                2
            ),
            'jobs_per_second': round(
                total_successful / total_duration if total_duration > 0 else 0,
                2
            ),
            'by_platform': {
                platform: metrics.to_dict()
                for platform, metrics in self.metrics.items()
            }
        }


# ============================================================================
# ASYNC TASK QUEUE
# ============================================================================

class AsyncTaskQueue:
    """
    Async task queue with concurrency control and rate limiting.
    Processes tasks in parallel with configurable workers and delays.
    """
    
    def __init__(self, max_workers: int = 5, delay_between_tasks: float = 0.5):
        self.max_workers = max_workers
        self.delay_between_tasks = delay_between_tasks
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Any] = []
        self.errors: List[tuple] = []
    
    async def add_task(self, coro, *args, **kwargs):
        """Add a coroutine task to the queue."""
        await self.queue.put((coro, args, kwargs))
    
    async def worker(self, worker_id: int):
        """Worker that processes tasks from queue with delays."""
        while True:
            try:
                coro, args, kwargs = await self.queue.get()
                
                try:
                    result = await coro(*args, **kwargs)
                    self.results.append(result)
                except Exception as e:
                    self.errors.append((coro.__name__, str(e)))
                    logger.error(f"Worker {worker_id} error: {e}")
                finally:
                    self.queue.task_done()
                    # Add delay between tasks to prevent rate limiting
                    await asyncio.sleep(self.delay_between_tasks)
                    
            except asyncio.CancelledError:
                break
    
    async def process_all(self):
        """Process all tasks in queue with multiple workers."""
        workers = [
            asyncio.create_task(self.worker(i))
            for i in range(self.max_workers)
        ]
        
        # Wait for all tasks to complete
        await self.queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)
        
        return self.results, self.errors


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Content deduplication
    dedup = ContentDeduplicator()
    
    job1 = {
        'job_title': 'Senior Consultant',
        'company': 'Accenture',
        'job_description': 'Looking for experienced consultant...',
        'job_url': 'https://linkedin.com/jobs/123'
    }
    
    job2 = {
        'job_title': 'Senior Consultant',
        'company': 'Accenture',
        'job_description': 'Looking for experienced consultant...',
        'job_url': 'https://indeed.com/jobs/456'  # Different URL, same job
    }
    
    is_dup1, reason1 = dedup.is_duplicate(job1)
    print(f"Job 1 duplicate: {is_dup1} ({reason1})")
    dedup.mark_as_seen(job1)
    
    is_dup2, reason2 = dedup.is_duplicate(job2)
    print(f"Job 2 duplicate: {is_dup2} ({reason2})")  # Should be True
    
    print(f"\nDeduplication stats: {dedup.get_stats()}")
