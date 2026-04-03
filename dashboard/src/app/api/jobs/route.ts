/**
 * API Gateway - Main Aggregation Endpoint
 * 
 * Fetches jobs from all sources (LinkedIn, Indeed, Naukri)
 * Normalizes, merges, and returns unified response
 * 
 * GET /api/jobs
 * Query params:
 *  - search: string (keyword search)
 *  - location: string (location filter)
 *  - source: string (linkedin|indeed|naukri)
 *  - type: string (employment type)
 *  - page: number (pagination)
 *  - limit: number (results per page)
 */

import { NextRequest, NextResponse } from 'next/server';
import { fetchAllJobs, filterJobs } from '@/lib/google-sheets';

export const dynamic = 'force-dynamic';
export const revalidate = 300; // Revalidate every 5 minutes

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    // Parse query parameters
    const searchParams = request.nextUrl.searchParams;
    const search = searchParams.get('search') || undefined;
    const location = searchParams.get('location') || undefined;
    const source = searchParams.get('source') || undefined;
    const type = searchParams.get('type') || undefined;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    // Fetch and filter jobs
    let jobs;
    let stats;

    if (search || location || source || type) {
      // Apply filters
      jobs = await filterJobs({ search, location, source, type });
      stats = {
        total: jobs.length,
        filtered: true,
      };
    } else {
      // Fetch all jobs
      const result = await fetchAllJobs();
      jobs = result.jobs;
      stats = result.stats;
    }

    // Pagination
    const totalPages = Math.ceil(jobs.length / limit);
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedJobs = jobs.slice(startIndex, endIndex);

    // Response metadata
    const response = {
      success: true,
      data: {
        jobs: paginatedJobs,
        pagination: {
          page,
          limit,
          total: jobs.length,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
        stats,
      },
      meta: {
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime,
      },
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('API Gateway error:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch jobs',
      },
      { status: 500 }
    );
  }
}
