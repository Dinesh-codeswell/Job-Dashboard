"""
JobSpy Configuration Loader
Loads settings from .env file for easy configuration management
"""

import os
from pathlib import Path
from typing import Optional, List


class JobSpyConfig:
    """Load and manage JobSpy configuration from .env file."""

    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration loader.

        Args:
            env_file: Path to .env file
        """
        self.env_file = Path(env_file)
        self._load_env()

    def _load_env(self):
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            print(f"⚠️  Warning: .env file not found at {self.env_file}")
            print(f"   Copy .env.example to .env and configure")
            return

        # Parse .env file
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    # Set as environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value

    # Google Sheets Configuration
    @property
    def google_sheet_id(self) -> Optional[str]:
        """Get Google Spreadsheet ID."""
        return os.environ.get('GOOGLE_SHEET_ID')

    @property
    def google_sheet_name(self) -> str:
        """Get Google Spreadsheet name."""
        return os.environ.get('GOOGLE_SHEET_NAME', 'India Consulting Jobs')

    @property
    def google_worksheet_name(self) -> str:
        """Get worksheet name."""
        return os.environ.get('GOOGLE_WORKSHEET_NAME', 'Jobs')

    @property
    def google_service_account_file(self) -> str:
        """Get service account file path."""
        return os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'google_sheets/service_account.json')

    # Scraping Configuration
    @property
    def default_job_boards(self) -> List[str]:
        """Get default job boards."""
        boards = os.environ.get('DEFAULT_JOB_BOARDS', 'naukri,indeed,linkedin')
        return [b.strip() for b in boards.split(',')]

    @property
    def default_results_per_city(self) -> int:
        """Get default results per city."""
        return int(os.environ.get('DEFAULT_RESULTS_PER_CITY', '30'))

    @property
    def default_hours_old(self) -> int:
        """Get default freshness window (hours)."""
        return int(os.environ.get('DEFAULT_HOURS_OLD', '48'))

    @property
    def default_job_type(self) -> str:
        """Get default job type."""
        return os.environ.get('DEFAULT_JOB_TYPE', 'fulltime')

    @property
    def default_cities(self) -> List[str]:
        """Get default cities."""
        cities = os.environ.get('DEFAULT_CITIES', 'Chennai,Mumbai,Pune,Gurugram,Bangalore,Hyderabad')
        return [c.strip() for c in cities.split(',')]

    # Output Configuration
    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return os.environ.get('OUTPUT_DIR', 'output/india_consulting')

    @property
    def use_google_sheets(self) -> bool:
        """Check if Google Sheets output is enabled."""
        return os.environ.get('USE_GOOGLE_SHEETS', 'true').lower() == 'true'

    @property
    def use_local_files(self) -> bool:
        """Check if local file output is enabled."""
        return os.environ.get('USE_LOCAL_FILES', 'true').lower() == 'true'

    @property
    def output_format(self) -> str:
        """Get output format."""
        return os.environ.get('OUTPUT_FORMAT', 'all')

    # Dashboard Configuration
    @property
    def dashboard_host(self) -> str:
        """Get dashboard host."""
        return os.environ.get('DASHBOARD_HOST', '0.0.0.0')

    @property
    def dashboard_port(self) -> int:
        """Get dashboard port."""
        return int(os.environ.get('DASHBOARD_PORT', '8080'))

    # Advanced Settings
    @property
    def max_workers(self) -> int:
        """Get maximum workers."""
        return int(os.environ.get('MAX_WORKERS', '3'))

    @property
    def verbose_level(self) -> int:
        """Get verbose level."""
        return int(os.environ.get('VERBOSE_LEVEL', '2'))

    @property
    def auto_remove_jobs_age_days(self) -> int:
        """Get auto-remove age threshold."""
        return int(os.environ.get('AUTO_REMOVE_JOBS_AGE_DAYS', '60'))


# Create global config instance
config = JobSpyConfig()


def get_config() -> JobSpyConfig:
    """Get global configuration instance."""
    return config


def print_config():
    """Print current configuration."""
    cfg = get_config()
    print("\n" + "="*60)
    print("📋 JobSpy Configuration")
    print("="*60)

    print("\n📊 Google Sheets:")
    print(f"   Spreadsheet ID: {cfg.google_sheet_id or 'Not set'}")
    print(f"   Spreadsheet Name: {cfg.google_sheet_name}")
    print(f"   Worksheet: {cfg.google_worksheet_name}")
    print(f"   Service Account: {cfg.google_service_account_file}")

    print("\n🔍 Scraping:")
    print(f"   Job Boards: {', '.join(cfg.default_job_boards)}")
    print(f"   Results/City: {cfg.default_results_per_city}")
    print(f"   Freshness: {cfg.default_hours_old} hours ({cfg.default_hours_old // 24} days)")
    print(f"   Job Type: {cfg.default_job_type}")
    print(f"   Cities: {', '.join(cfg.default_cities[:5])}...")

    print("\n💾 Output:")
    print(f"   Directory: {cfg.output_dir}")
    print(f"   Google Sheets: {'✅' if cfg.use_google_sheets else '❌'}")
    print(f"   Local Files: {'✅' if cfg.use_local_files else '❌'}")
    print(f"   Format: {cfg.output_format}")

    print("\n⚙️  Advanced:")
    print(f"   Workers: {cfg.max_workers}")
    print(f"   Verbose: {cfg.verbose_level}")
    print(f"   Auto-remove: {cfg.auto_remove_jobs_age_days} days")

    print("\n" + "="*60)
    print("💡 Edit .env to change configuration")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_config()
