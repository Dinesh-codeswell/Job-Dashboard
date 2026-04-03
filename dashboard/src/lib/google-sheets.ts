/**
 * Google Sheets Data Fetcher
 * 
 * Fetches job data from Google Sheets API
 * Used by API Gateway endpoints
 */

import { google } from 'googleapis';

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
  source: 'linkedin' | 'indeed' | 'naukri';
  logo?: string;
  posted_date: string;
  employment_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  date_added: string;
}

export interface SheetData {
  jobs: Job[];
  lastUpdated: string;
}

// Google Sheets configuration
const SPREADSHEET_ID = process.env.GOOGLE_SHEET_ID || '';
const CREDENTIALS_FILE = process.env.GOOGLE_CREDENTIALS_FILE || 'credentials.json';

let cachedAuth: any = null;

/**
 * Get authenticated Google Sheets client
 */
async function getSheetsClient() {
  if (cachedAuth) {
    return cachedAuth;
  }

  try {
    const credentials = require(`../../${CREDENTIALS_FILE}`);
    
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    cachedAuth = auth;
    return auth;
  } catch (error) {
    console.error('Failed to initialize Google Sheets client:', error);
    throw new Error('Google Sheets authentication failed. Check credentials file.');
  }
}

/**
 * Fetch jobs from a specific worksheet
 */
async function fetchJobsFromSheet(worksheetName: string, source: 'linkedin' | 'indeed' | 'naukri'): Promise<Job[]> {
  try {
    const auth = await getSheetsClient();
    const sheets = google.sheets({ version: 'v4', auth });

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${worksheetName}!A2:J`, // Skip header row
    });

    const rows = response.data.values;

    if (!rows || rows.length === 0) {
      return [];
    }

    // Map sheet columns to Job interface
    // Columns: A=Company, B=Logo, C=Title, D=Type, E=Posted, F=Location, G=Description, H=URL, I=City, J=Date Added
    const jobs: Job[] = rows.map((row, index) => ({
      id: `${source}-${index}-${Date.now()}`,
      title: row[2] || 'N/A', // Column C
      company: row[0] || 'Unknown', // Column A
      location: row[5] || 'Not specified', // Column F
      description: cleanDescription(row[6] || ''), // Column G
      url: row[7] || '#', // Column H
      source: source,
      logo: row[1] || undefined, // Column B
      posted_date: row[4] || 'Unknown', // Column E
      employment_type: row[3] || 'Full-time', // Column D
      date_added: row[9] || new Date().toISOString(), // Column J
    }));

    return jobs;
  } catch (error) {
    console.error(`Error fetching ${worksheetName}:`, error);
    return [];
  }
}

/**
 * Clean job description for display
 */
function cleanDescription(description: string): string {
  if (!description) return '';
  
  // Remove LinkedIn artifacts
  description = description.replace(/… more/g, '');
  description = description.replace(/\.\.\. more/g, '');
  description = description.replace(/Show less/g, '');
  description = description.replace(/Show more/g, '');
  
  // Truncate if too long (preview)
  if (description.length > 500) {
    description = description.substring(0, 500) + '...';
  }
  
  return description.trim();
}

/**
 * Fetch jobs from all sheets and merge
 */
export async function fetchAllJobs(): Promise<{ jobs: Job[]; stats: any }> {
  const startTime = Date.now();
  
  // Fetch from all sheets in parallel
  const [linkedinJobs, indeedJobs, naukriJobs] = await Promise.all([
    fetchJobsFromSheet('LinkedIn_Jobs', 'linkedin'),
    fetchJobsFromSheet('Indeed_Jobs', 'indeed'),
    fetchJobsFromSheet('Naukri_Jobs', 'naukri'),
  ]);

  // Merge all jobs
  const allJobs = [...linkedinJobs, ...indeedJobs, ...naukriJobs];

  // Sort by posted date (most recent first)
  allJobs.sort((a, b) => {
    const dateA = parseDate(a.posted_date);
    const dateB = parseDate(b.posted_date);
    return dateB.getTime() - dateA.getTime();
  });

  // Calculate statistics
  const stats = {
    total: allJobs.length,
    linkedin: linkedinJobs.length,
    indeed: indeedJobs.length,
    naukri: naukriJobs.length,
    companies: new Set(allJobs.map(j => j.company)).size,
    locations: new Set(allJobs.map(j => j.location)).size,
    fetchTime: Date.now() - startTime,
  };

  return {
    jobs: allJobs,
    stats,
  };
}

/**
 * Parse date from various formats
 */
function parseDate(dateStr: string): Date {
  if (!dateStr) return new Date(0);
  
  // Try parsing "X days ago" format
  const daysAgoMatch = dateStr.match(/(\d+)\s*days?\s*ago/i);
  if (daysAgoMatch) {
    const days = parseInt(daysAgoMatch[1]);
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date;
  }

  // Try parsing "today"
  if (dateStr.toLowerCase().includes('today')) {
    return new Date();
  }

  // Try parsing "yesterday"
  if (dateStr.toLowerCase().includes('yesterday')) {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return date;
  }

  // Try standard date parsing
  const parsed = new Date(dateStr);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }

  // Default to old date if parsing fails
  return new Date(0);
}

/**
 * Get job by ID
 */
export async function getJobById(jobId: string): Promise<Job | null> {
  const { jobs } = await fetchAllJobs();
  return jobs.find(job => job.id === jobId) || null;
}

/**
 * Filter jobs by criteria
 */
export async function filterJobs(filters: {
  search?: string;
  location?: string;
  source?: string;
  type?: string;
}): Promise<Job[]> {
  const { jobs } = await fetchAllJobs();
  
  let filtered = jobs;

  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filtered = filtered.filter(job =>
      job.title.toLowerCase().includes(searchLower) ||
      job.company.toLowerCase().includes(searchLower) ||
      job.description.toLowerCase().includes(searchLower)
    );
  }

  if (filters.location) {
    const locationLower = filters.location.toLowerCase();
    filtered = filtered.filter(job =>
      job.location.toLowerCase().includes(locationLower)
    );
  }

  if (filters.source) {
    filtered = filtered.filter(job => job.source === filters.source);
  }

  if (filters.type) {
    const typeLower = filters.type.toLowerCase();
    filtered = filtered.filter(job =>
      job.employment_type?.toLowerCase().includes(typeLower)
    );
  }

  return filtered;
}
