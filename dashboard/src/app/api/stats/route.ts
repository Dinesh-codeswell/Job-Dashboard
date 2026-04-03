/**
 * Dashboard Statistics Endpoint
 * 
 * GET /api/stats
 * Returns aggregated statistics for dashboard
 */

import { NextRequest, NextResponse } from 'next/server';
import { fetchAllJobs } from '@/lib/google-sheets';

export const dynamic = 'force-dynamic';
export const revalidate = 300; // Revalidate every 5 minutes

export async function GET(request: NextRequest) {
  try {
    const { jobs, stats } = await fetchAllJobs();

    // Calculate additional statistics
    const recentJobs = jobs.filter(job => {
      const jobDate = new Date(job.posted_date);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - jobDate.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays <= 7; // Jobs from last 7 days
    });

    const topCompanies = jobs
      .reduce((acc, job) => {
        acc[job.company] = (acc[job.company] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
      .entries()
      .toArray()
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([company, count]) => ({ company, count }));

    const topLocations = jobs
      .reduce((acc, job) => {
        acc[job.location] = (acc[job.location] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
      .entries()
      .toArray()
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([location, count]) => ({ location, count }));

    return NextResponse.json({
      success: true,
      data: {
        overview: stats,
        recent: {
          count: recentJobs.length,
          percentage: ((recentJobs.length / stats.total) * 100).toFixed(1),
        },
        topCompanies,
        topLocations,
        sourceBreakdown: [
          { name: 'LinkedIn', count: stats.linkedin, percentage: ((stats.linkedin / stats.total) * 100).toFixed(1) },
          { name: 'Indeed', count: stats.indeed, percentage: ((stats.indeed / stats.total) * 100).toFixed(1) },
          { name: 'Naukri', count: stats.naukri, percentage: ((stats.naukri / stats.total) * 100).toFixed(1) },
        ],
      },
      meta: {
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error('Stats error:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch statistics',
      },
      { status: 500 }
    );
  }
}

// Helper to convert object entries to array (TypeScript compatibility)
declare global {
  interface ObjectConstructor {
    entries<T>(o: T): [Extract<keyof T, string>, T[keyof T]][];
  }
}

Object.entries = function<T>(o: T) {
  return Object.entries(o as any) as [Extract<keyof T, string>, T[keyof T]][];
};
