"""
Job Storage Module

Handles automatic storage of scraped jobs to:
- Local files (CSV, Excel, JSON, Parquet)
- Google Sheets
- Notion databases
- SQLite database

Usage:
    from linkedin_scraper.integrations.job_storage import JobStorage
    
    storage = JobStorage()
    storage.save_all(df, output_dir="output/jobs")
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


class JobStorage:
    """
    Unified storage manager for scraped jobs.
    
    Supports multiple output formats and destinations.
    
    Example:
        storage = JobStorage()
        storage.save_all(
            df,
            output_dir="output/jobs",
            save_to_csv=True,
            save_to_excel=True,
            save_to_google_sheets=True
        )
    """
    
    def __init__(
        self,
        output_dir: str = "output/jobs",
        google_sheet_id: Optional[str] = None,
        google_credentials_file: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        notion_api_key: Optional[str] = None,
    ):
        """
        Initialize job storage manager.
        
        Args:
            output_dir: Base directory for local file output
            google_sheet_id: Google Spreadsheet ID (optional)
            google_credentials_file: Path to Google credentials JSON (optional)
            notion_database_id: Notion database ID (optional)
            notion_api_key: Notion API integration key (optional)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.google_sheet_id = google_sheet_id
        self.google_credentials_file = google_credentials_file
        self.notion_database_id = notion_database_id
        self.notion_api_key = notion_api_key
        
        logger.info(f"JobStorage initialized. Output dir: {self.output_dir}")
    
    def generate_filename(self, prefix: str = "jobs", extension: str = "csv") -> str:
        """
        Generate timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            Filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
    
    def save_to_csv(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_timestamp: bool = True
    ) -> str:
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame with job data
            filename: Output filename (auto-generated if not provided)
            include_timestamp: Add timestamp to filename
            
        Returns:
            Path to saved file
        """
        if len(df) == 0:
            logger.warning("No data to save to CSV")
            return ""
        
        if filename is None:
            filename = self.generate_filename("jobs", "csv") if include_timestamp else "jobs.csv"
        
        filepath = self.output_dir / filename
        
        # Ensure all columns are string-compatible
        df_to_save = df.copy()
        for col in df_to_save.columns:
            if df_to_save[col].dtype == 'object':
                df_to_save[col] = df_to_save[col].fillna('').astype(str)
            else:
                df_to_save[col] = df_to_save[col].fillna('')
        
        df_to_save.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} jobs to CSV: {filepath}")
        
        return str(filepath)
    
    def save_to_excel(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_summary: bool = True,
        split_by_site: bool = True
    ) -> str:
        """
        Save DataFrame to Excel file with optional sheets per platform.
        
        Args:
            df: DataFrame with job data
            filename: Output filename (auto-generated if not provided)
            include_summary: Include summary statistics sheet
            split_by_site: Create separate sheet for each platform
            
        Returns:
            Path to saved file
        """
        if len(df) == 0:
            logger.warning("No data to save to Excel")
            return ""
        
        if filename is None:
            filename = self.generate_filename("jobs_report", "xlsx")
        
        filepath = self.output_dir / filename
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Summary sheet
                if include_summary and 'site' in df.columns:
                    summary = df.groupby('site').agg({
                        'title': 'count',
                        'company': lambda x: x.nunique()
                    }).reset_index()
                    summary.columns = ['Platform', 'Jobs', 'Unique Companies']
                    summary['Total Jobs'] = summary['Jobs'].sum()
                    summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # All jobs sheet
                df.to_excel(writer, sheet_name='All Jobs', index=False)
                
                # Per-platform sheets
                if split_by_site and 'site' in df.columns:
                    for site in df['site'].unique():
                        site_df = df[df['site'] == site]
                        sheet_name = f"{site.title()} Jobs"[:31]  # Excel limit
                        site_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Saved {len(df)} jobs to Excel: {filepath}")
            return str(filepath)
        except ImportError:
            logger.warning("openpyxl not installed. Install with: pip install openpyxl")
            # Fallback to CSV
            return self.save_to_csv(df, filename.replace('.xlsx', '.csv'))
    
    def save_to_json(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        orient: str = 'records',
        indent: int = 2
    ) -> str:
        """
        Save DataFrame to JSON file.
        
        Args:
            df: DataFrame with job data
            filename: Output filename
            orient: JSON orientation ('records', 'index', etc.)
            indent: JSON indentation level
            
        Returns:
            Path to saved file
        """
        if len(df) == 0:
            logger.warning("No data to save to JSON")
            return ""
        
        if filename is None:
            filename = self.generate_filename("jobs", "json")
        
        filepath = self.output_dir / filename
        
        # Convert to JSON-serializable format
        df_copy = df.copy()
        for col in df_copy.columns:
            df_copy[col] = df_copy[col].fillna('')
        
        df_copy.to_json(filepath, orient=orient, indent=indent, force_ascii=False)
        logger.info(f"Saved {len(df)} jobs to JSON: {filepath}")
        
        return str(filepath)
    
    def save_to_parquet(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None
    ) -> str:
        """
        Save DataFrame to Parquet file (efficient binary format).
        
        Args:
            df: DataFrame with job data
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        if len(df) == 0:
            logger.warning("No data to save to Parquet")
            return ""
        
        if filename is None:
            filename = self.generate_filename("jobs", "parquet")
        
        filepath = self.output_dir / filename
        
        df.to_parquet(filepath, index=False, engine='pyarrow')
        logger.info(f"Saved {len(df)} jobs to Parquet: {filepath}")
        
        return str(filepath)
    
    def save_to_google_sheets(
        self,
        df: pd.DataFrame,
        sheet_name: str = "Jobs",
        clear_first: bool = False
    ) -> bool:
        """
        Save DataFrame to Google Sheets.
        
        Args:
            df: DataFrame with job data
            sheet_name: Target sheet name
            clear_first: Clear existing data before writing
            
        Returns:
            True if successful
        """
        if len(df) == 0:
            logger.warning("No data to save to Google Sheets")
            return False
        
        if not self.google_sheet_id or not self.google_credentials_file:
            logger.warning("Google Sheets not configured. Set google_sheet_id and google_credentials_file")
            return False
        
        try:
            from .google_sheets import GoogleSheetsIntegration
            
            integration = GoogleSheetsIntegration(
                sheet_id=self.google_sheet_id,
                credentials_file=self.google_credentials_file
            )
            
            # Prepare data
            headers = df.columns.tolist()
            data = df.fillna('').values.tolist()
            
            # Write to sheet
            integration.write_jobs(sheet_name, headers, data, clear_first)
            logger.info(f"Saved {len(df)} jobs to Google Sheets: {sheet_name}")
            
            return True
        except ImportError as e:
            logger.error(f"Google Sheets integration not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save to Google Sheets: {e}")
            return False
    
    def save_to_notion(
        self,
        df: pd.DataFrame,
        database_id: Optional[str] = None
    ) -> bool:
        """
        Save jobs to Notion database.
        
        Args:
            df: DataFrame with job data
            database_id: Notion database ID (overrides constructor value)
            
        Returns:
            True if successful
        """
        if len(df) == 0:
            logger.warning("No data to save to Notion")
            return False
        
        notion_db = database_id or self.notion_database_id
        if not notion_db or not self.notion_api_key:
            logger.warning("Notion not configured. Set notion_database_id and notion_api_key")
            return False
        
        try:
            from .notion import NotionIntegration
            
            integration = NotionIntegration(api_key=self.notion_api_key)
            
            success_count = 0
            for _, row in df.iterrows():
                try:
                    properties = {
                        "Name": {"title": [{"text": {"content": str(row.get('title', ''))}}]},
                        "Company": {"rich_text": [{"text": {"content": str(row.get('company', ''))}}]},
                        "Location": {"rich_text": [{"text": {"content": str(row.get('location', ''))}}]},
                        "URL": {"url": str(row.get('job_url', ''))},
                        "Platform": {"select": {"name": str(row.get('site', ''))}},
                    }
                    
                    integration.create_page(database_id=notion_db, properties=properties)
                    success_count += 1
                except Exception as e:
                    logger.debug(f"Failed to add job to Notion: {e}")
                    continue
            
            logger.info(f"Saved {success_count}/{len(df)} jobs to Notion database")
            return success_count > 0
        except ImportError as e:
            logger.error(f"Notion integration not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to save to Notion: {e}")
            return False
    
    def save_to_sqlite(
        self,
        df: pd.DataFrame,
        table_name: str = "jobs",
        database_path: Optional[str] = None
    ) -> str:
        """
        Save DataFrame to SQLite database.
        
        Args:
            df: DataFrame with job data
            table_name: Database table name
            database_path: Path to SQLite database file
            
        Returns:
            Path to database file
        """
        if len(df) == 0:
            logger.warning("No data to save to SQLite")
            return ""
        
        if database_path is None:
            database_path = self.output_dir / "jobs.db"
        else:
            database_path = Path(database_path)
        
        # Append to existing table
        if_exists = 'append' if database_path.exists() else 'replace'
        
        df.to_sql(table_name, f"sqlite:///{database_path}", if_exists=if_exists, index=False)
        logger.info(f"Saved {len(df)} jobs to SQLite: {database_path}")
        
        return str(database_path)
    
    def save_all(
        self,
        df: pd.DataFrame,
        output_dir: Optional[str] = None,
        save_csv: bool = True,
        save_excel: bool = True,
        save_json: bool = False,
        save_parquet: bool = False,
        save_google_sheets: bool = False,
        save_notion: bool = False,
        save_sqlite: bool = False
    ) -> Dict[str, str]:
        """
        Save DataFrame to multiple formats simultaneously.
        
        Args:
            df: DataFrame with job data
            output_dir: Override output directory
            save_csv: Save to CSV
            save_excel: Save to Excel
            save_json: Save to JSON
            save_parquet: Save to Parquet
            save_google_sheets: Save to Google Sheets
            save_notion: Save to Notion
            save_sqlite: Save to SQLite
            
        Returns:
            Dictionary of format -> filepath
        """
        if len(df) == 0:
            logger.warning("No data to save")
            return {}
        
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        if save_csv:
            try:
                results['csv'] = self.save_to_csv(df)
            except Exception as e:
                logger.error(f"Failed to save CSV: {e}")
        
        if save_excel:
            try:
                results['excel'] = self.save_to_excel(df)
            except Exception as e:
                logger.error(f"Failed to save Excel: {e}")
        
        if save_json:
            try:
                results['json'] = self.save_to_json(df)
            except Exception as e:
                logger.error(f"Failed to save JSON: {e}")
        
        if save_parquet:
            try:
                results['parquet'] = self.save_to_parquet(df)
            except Exception as e:
                logger.error(f"Failed to save Parquet: {e}")
        
        if save_google_sheets:
            try:
                success = self.save_to_google_sheets(df)
                results['google_sheets'] = "✅" if success else "❌"
            except Exception as e:
                logger.error(f"Failed to save to Google Sheets: {e}")
                results['google_sheets'] = "❌"
        
        if save_notion:
            try:
                success = self.save_to_notion(df)
                results['notion'] = "✅" if success else "❌"
            except Exception as e:
                logger.error(f"Failed to save to Notion: {e}")
                results['notion'] = "❌"
        
        if save_sqlite:
            try:
                results['sqlite'] = self.save_to_sqlite(df)
            except Exception as e:
                logger.error(f"Failed to save SQLite: {e}")
        
        logger.info(f"Storage complete. Saved to: {', '.join(results.keys())}")
        
        return results


def auto_save_jobs(
    df: pd.DataFrame,
    output_dir: str = "output/jobs",
    formats: List[str] = None
) -> Dict[str, str]:
    """
    Convenience function to automatically save jobs to multiple formats.
    
    Args:
        df: DataFrame with job data
        output_dir: Output directory
        formats: List of formats to save ('csv', 'excel', 'json', 'parquet', 'sqlite')
        
    Returns:
        Dictionary of format -> filepath
        
    Example:
        df = scrape_multi_platform(["indeed", "naukri"], "python developer")
        auto_save_jobs(df, formats=['csv', 'excel', 'sqlite'])
    """
    if formats is None:
        formats = ['csv', 'excel']
    
    storage = JobStorage(output_dir=output_dir)
    
    return storage.save_all(
        df,
        save_csv='csv' in formats,
        save_excel='excel' in formats,
        save_json='json' in formats,
        save_parquet='parquet' in formats,
        save_sqlite='sqlite' in formats
    )


__all__ = [
    "JobStorage",
    "auto_save_jobs",
]
