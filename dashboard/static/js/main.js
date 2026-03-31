/**
 * Main Dashboard JavaScript for Consulting Jobs Dashboard
 * Handles job listing, pagination, filters, and auto-refresh
 */

// ============================================================================
// Dashboard State
// ============================================================================

const Dashboard = {
    // Current state
    currentPage: 1,
    totalPages: 1,
    limit: 30,
    filters: {
        search: '',
        city: '',
        type: ''
    },
    
    // Auto-refresh
    autoRefreshInterval: 60, // seconds
    refreshCountdown: 60,
    refreshTimer: null,
    lastUpdated: null,
    
    // Cache
    jobs: [],
    stats: null,
    cities: [],
    employmentTypes: []
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});

async function initializeDashboard() {
    // Load initial data
    await Promise.all([
        loadStats(),
        loadCities(),
        loadEmploymentTypes(),
        loadJobs()
    ]);
    
    // Setup event listeners
    setupEventListeners();
    
    // Start auto-refresh
    startAutoRefresh();
    
    console.log('Dashboard initialized');
}

// ============================================================================
// Data Loading
// ============================================================================

async function loadJobs(page = 1) {
    try {
        showLoading();
        
        const response = await API.getJobs(page, Dashboard.limit, Dashboard.filters);
        
        if (response.success) {
            Dashboard.jobs = response.jobs;
            Dashboard.currentPage = response.pagination.page;
            Dashboard.totalPages = response.pagination.total_pages;
            
            renderJobs();
            renderPagination();
            updateResultsCount(response.pagination.total);
        } else {
            showError('Failed to load jobs');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs. Please refresh the page.');
    }
}

async function loadStats() {
    try {
        const response = await API.getStats();
        
        if (response.success) {
            Dashboard.stats = response.stats;
            Dashboard.lastUpdated = response.stats.last_updated;
            renderStats();
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadCities() {
    try {
        const response = await API.getCities();
        
        if (response.success) {
            Dashboard.cities = response.cities;
            populateCityFilter();
        }
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

async function loadEmploymentTypes() {
    try {
        const response = await API.getEmploymentTypes();
        
        if (response.success) {
            Dashboard.employmentTypes = response.types;
            populateTypeFilter();
        }
    } catch (error) {
        console.error('Error loading employment types:', error);
    }
}

// ============================================================================
// Rendering
// ============================================================================

function renderJobs() {
    const grid = document.getElementById('jobsGrid');
    
    if (!Dashboard.jobs || Dashboard.jobs.length === 0) {
        grid.innerHTML = `
            <div class="loading-state" style="grid-column: 1 / -1;">
                <div class="error-icon">📭</div>
                <h2>No Jobs Found</h2>
                <p>Try adjusting your search or filters</p>
                <button class="btn btn-primary" onclick="clearAllFilters()">Clear Filters</button>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = Dashboard.jobs.map(job => createJobCard(job)).join('');
}

function createJobCard(job) {
    const title = Utils.escapeHtml(job.job_title || 'Position');
    const company = Utils.escapeHtml(job.company || 'Company');
    const location = Utils.escapeHtml(job.location || 'Location');
    const type = Utils.escapeHtml(job.employment_type || 'Full-time');
    const posted = Utils.formatRelativeTime(job.posted_date);
    const city = Utils.escapeHtml(job.search_city || '');
    
    return `
        <div class="job-card" onclick="navigateToJob('${job.id}')">
            <div class="job-card-header">
                <div>
                    <h3 class="job-card-title">${title}</h3>
                    <p class="job-card-company">${company}</p>
                </div>
            </div>
            
            <div class="job-card-badges">
                <span class="badge badge-type">${type}</span>
                <span class="badge badge-location">${city || location}</span>
            </div>
            
            <div class="job-card-meta">
                <div class="meta-item">
                    <span class="meta-icon">⏰</span>
                    <span>${posted}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-icon">📍</span>
                    <span>${location}</span>
                </div>
            </div>
            
            <div class="job-card-footer">
                <button class="view-job-btn">View Details →</button>
            </div>
        </div>
    `;
}

function renderPagination() {
    const container = document.getElementById('pagination');
    
    if (Dashboard.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = `
        <button onclick="goToPage(${Dashboard.currentPage - 1})" 
                ${Dashboard.currentPage === 1 ? 'disabled' : ''}>
            ← Previous
        </button>
    `;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, Dashboard.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(Dashboard.totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="pagination-info">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button onclick="goToPage(${i})" 
                    class="${i === Dashboard.currentPage ? 'active' : ''}">
                ${i}
            </button>
        `;
    }
    
    if (endPage < Dashboard.totalPages) {
        if (endPage < Dashboard.totalPages - 1) {
            html += `<span class="pagination-info">...</span>`;
        }
        html += `<button onclick="goToPage(${Dashboard.totalPages})">${Dashboard.totalPages}</button>`;
    }
    
    html += `
        <button onclick="goToPage(${Dashboard.currentPage + 1})" 
                ${Dashboard.currentPage === Dashboard.totalPages ? 'disabled' : ''}>
            Next →
        </button>
        <span class="pagination-info" style="margin-left: 1rem;">
            Page ${Dashboard.currentPage} of ${Dashboard.totalPages}
        </span>
    `;
    
    container.innerHTML = html;
}

function renderStats() {
    if (!Dashboard.stats) return;
    
    const { total_jobs, cities, companies, last_updated } = Dashboard.stats;
    
    document.getElementById('totalJobs').textContent = total_jobs || 0;
    document.getElementById('totalCities').textContent = Object.keys(cities || {}).length;
    document.getElementById('totalCompanies').textContent = Object.keys(companies || {}).length;
    
    if (last_updated) {
        const date = new Date(last_updated);
        document.getElementById('lastUpdated').textContent = Utils.formatDate(last_updated);
    }
}

function populateCityFilter() {
    const select = document.getElementById('cityFilter');
    select.innerHTML = '<option value="">All Cities</option>' +
        Dashboard.cities.map(city => `<option value="${Utils.escapeHtml(city)}">${Utils.escapeHtml(city)}</option>`).join('');
}

function populateTypeFilter() {
    const select = document.getElementById('typeFilter');
    select.innerHTML = '<option value="">All Types</option>' +
        Dashboard.employmentTypes.map(type => `<option value="${Utils.escapeHtml(type)}">${Utils.escapeHtml(type)}</option>`).join('');
}

function updateResultsCount(total) {
    document.getElementById('resultsCount').textContent = 
        `${total} job${total !== 1 ? 's' : ''} found`;
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('searchInput');
    const debouncedSearch = Utils.debounce((e) => {
        Dashboard.filters.search = e.target.value.trim();
        goToPage(1);
    }, 500);
    searchInput.addEventListener('input', debouncedSearch);
    
    // City filter
    document.getElementById('cityFilter').addEventListener('change', (e) => {
        Dashboard.filters.city = e.target.value;
        goToPage(1);
    });
    
    // Type filter
    document.getElementById('typeFilter').addEventListener('change', (e) => {
        Dashboard.filters.type = e.target.value;
        goToPage(1);
    });
    
    // Apply filters button
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    
    // Clear filters button
    document.getElementById('clearFilters').addEventListener('click', clearAllFilters);
    
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', handleManualRefresh);
}

// ============================================================================
// Navigation & Actions
// ============================================================================

function navigateToJob(jobId) {
    // Ensure jobId is properly encoded for URL
    const encodedId = encodeURIComponent(jobId);
    window.location.href = `/job/${encodedId}`;
}

function goToPage(page) {
    if (page < 1 || page > Dashboard.totalPages) return;
    Dashboard.currentPage = page;
    loadJobs(page);
    Utils.scrollToElement(document.querySelector('.filters-section'), 100);
}

function applyFilters() {
    goToPage(1);
}

function clearAllFilters() {
    Dashboard.filters = { search: '', city: '', type: '' };
    document.getElementById('searchInput').value = '';
    document.getElementById('cityFilter').value = '';
    document.getElementById('typeFilter').value = '';
    goToPage(1);
}

// ============================================================================
// Auto-Refresh
// ============================================================================

function startAutoRefresh() {
    Dashboard.refreshCountdown = Dashboard.autoRefreshInterval;
    updateRefreshIndicator();
    
    Dashboard.refreshTimer = setInterval(() => {
        Dashboard.refreshCountdown--;
        updateRefreshIndicator();
        
        if (Dashboard.refreshCountdown <= 0) {
            autoRefresh();
        }
    }, 1000);
}

function updateRefreshIndicator() {
    const indicator = document.getElementById('refreshCountdown');
    if (indicator) {
        indicator.textContent = Dashboard.refreshCountdown;
    }
}

async function autoRefresh() {
    try {
        const response = await API.getStats();
        
        if (response.success) {
            const newLastUpdated = response.stats.last_updated;
            
            // Check if data has changed
            if (newLastUpdated !== Dashboard.lastUpdated) {
                showNewJobsNotification();
            }
            
            Dashboard.lastUpdated = newLastUpdated;
            Dashboard.refreshCountdown = Dashboard.autoRefreshInterval;
        }
    } catch (error) {
        console.error('Auto-refresh failed:', error);
    }
}

function handleManualRefresh() {
    Dashboard.refreshCountdown = Dashboard.autoRefreshInterval;
    loadJobs(Dashboard.currentPage);
    loadStats();
    Utils.showToast('Data refreshed!', 'success');
}

function showNewJobsNotification() {
    const indicator = document.getElementById('autoRefreshIndicator');
    if (indicator) {
        indicator.style.background = 'rgba(16, 185, 129, 0.1)';
        indicator.style.padding = '0.5rem 1rem';
        indicator.style.borderRadius = 'var(--radius-md)';
        indicator.innerHTML = '<span class="pulse"></span><span>New jobs available! Refreshing...</span>';
        
        setTimeout(() => {
            indicator.style.background = '';
            indicator.style.padding = '';
            indicator.style.borderRadius = '';
            loadJobs(Dashboard.currentPage);
            loadStats();
        }, 2000);
    }
}

// ============================================================================
// UI Helpers
// ============================================================================

function showLoading() {
    const grid = document.getElementById('jobsGrid');
    if (grid && grid.innerHTML === '') {
        grid.innerHTML = `
            <div class="loading-state" style="grid-column: 1 / -1;">
                <div class="spinner"></div>
                <p>Loading jobs...</p>
            </div>
        `;
    }
}

function showError(message) {
    const grid = document.getElementById('jobsGrid');
    grid.innerHTML = `
        <div class="error-state" style="grid-column: 1 / -1;">
            <div class="error-icon">❌</div>
            <h2>Error</h2>
            <p>${Utils.escapeHtml(message)}</p>
            <button class="btn btn-primary" onclick="loadJobs()">Try Again</button>
        </div>
    `;
}

// ============================================================================
// Expose functions globally
// ============================================================================

window.Dashboard = Dashboard;
window.navigateToJob = navigateToJob;
window.goToPage = goToPage;
window.applyFilters = applyFilters;
window.clearAllFilters = clearAllFilters;
window.handleManualRefresh = handleManualRefresh;
