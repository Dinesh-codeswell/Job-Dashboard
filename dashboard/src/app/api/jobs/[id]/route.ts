/**
 * Get Single Job Endpoint
 * 
 * GET /api/jobs/[id]
 */

import { NextRequest, NextResponse } from 'next/server';
import { getJobById } from '@/lib/google-sheets';

export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const job = await getJobById(params.id);

    if (!job) {
      return NextResponse.json(
        { success: false, error: 'Job not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: { job },
    });
  } catch (error) {
    console.error('Error fetching job:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch job',
      },
      { status: 500 }
    );
  }
}
