/**
 * Main Dashboard JavaScript for Consulting Jobs Dashboard
 * Enhanced with modern UX patterns and performance optimizations
 */

// ============================================================================
// Dashboard State
// ============================================================================

const Dashboard = {
    // Current state
    currentPage: 1,
    totalPages: 1,
    limit: 11,
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
    employmentTypes: [],
    
    // Performance
    isLoading: false,
    observer: null
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    setupScrollObserver();
    setupKeyboardShortcuts();
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        const urlParams = new URLSearchParams(window.location.search);
        const pageFromURL = parseInt(urlParams.get('page'));
        if (!isNaN(pageFromURL) && pageFromURL > 0) {
            Dashboard.currentPage = pageFromURL;
            loadJobs(pageFromURL);
        }
    });
});

async function initializeDashboard() {
    try {
        // Read page number from URL if present
        const urlParams = new URLSearchParams(window.location.search);
        const pageFromURL = parseInt(urlParams.get('page'));
        const startPage = (!isNaN(pageFromURL) && pageFromURL > 0) ? pageFromURL : 1;
        
        // Load initial data - handle errors individually to prevent complete failure
        const loadPromises = [
            loadStats().catch(err => console.warn('Stats load failed:', err)),
            loadCities().catch(err => console.warn('Cities load failed:', err)),
            loadEmploymentTypes().catch(err => console.warn('Employment types load failed:', err)),
            loadJobs(startPage).catch(err => {
                console.error('Jobs load failed:', err);
                throw err; // Jobs are critical, so re-throw
            })
        ];
        
        await Promise.all(loadPromises);

        // Setup event listeners
        setupEventListeners();

        // Start auto-refresh
        startAutoRefresh();

        // Setup header scroll effect
        setupHeaderScroll();

        console.log('✅ Dashboard initialized');
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        // Only show error if jobs failed to load
        if (!Dashboard.jobs || Dashboard.jobs.length === 0) {
            showError('Failed to load jobs. Please try again.');
        }
    }
}

function setupScrollObserver() {
    // Lazy load job cards as they enter viewport
    Dashboard.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                const index = card.dataset.index;
                if (index !== undefined) {
                    card.style.setProperty('--index', index);
                }
                Dashboard.observer.unobserve(card);
            }
        });
    }, { threshold: 0.1 });
}

function setupHeaderScroll() {
    const header = document.querySelector('.header');
    if (!header) return;

    const handleScroll = Utils.debounce(() => {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }, 10);

    window.addEventListener('scroll', handleScroll, { passive: true });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // '/' to focus search
        if (e.key === '/' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // 'r' to refresh
        if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            handleManualRefresh();
        }

        // 'j' for next page
        if (e.key === 'j' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            if (Dashboard.currentPage < Dashboard.totalPages) {
                goToPage(Dashboard.currentPage + 1);
            }
        }

        // 'k' for previous page
        if (e.key === 'k' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            if (Dashboard.currentPage > 1) {
                goToPage(Dashboard.currentPage - 1);
            }
        }
    });
}

// ============================================================================
// Data Loading
// ============================================================================

async function loadJobs(page = 1) {
    if (Dashboard.isLoading) {
        console.log('Already loading, skipping...');
        return;
    }

    try {
        Dashboard.isLoading = true;
        showSkeletonLoading();
        showLoadingProgress();

        console.log('Loading jobs:', { page, limit: Dashboard.limit, filters: Dashboard.filters });

        const response = await API.getJobs(page, Dashboard.limit, Dashboard.filters);

        console.log('Jobs response:', response);

        if (response.success || (response.jobs && response.jobs.length >= 0)) {
            Dashboard.jobs = response.jobs || [];
            Dashboard.currentPage = response.pagination?.page || page;
            Dashboard.totalPages = response.pagination?.total_pages || 1;
            
            // Update the total jobs count to match the API response
            const totalFromAPI = response.pagination?.total || 0;
            if (Dashboard.stats) {
                Dashboard.stats.total_jobs = totalFromAPI;
            }

            // Hide skeleton and show actual jobs
            hideSkeletonLoading();
            renderJobs();
            renderPagination();
            updateResultsCount(totalFromAPI);
            
            // Also update the header stat to match
            animateValue('totalJobs', 0, totalFromAPI, 500);

            // Hide error if previously shown
            const errorEl = document.querySelector('.error-state');
            if (errorEl && Dashboard.jobs.length > 0) {
                errorEl.remove();
            }
        } else {
            console.error('API returned unsuccessful response:', response);
            // Don't show error immediately, might be temporary
            if (Dashboard.jobs.length === 0) {
                // Keep showing skeletons
            }
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        // Only show error if we have no jobs at all
        if (Dashboard.jobs.length === 0) {
            hideSkeletonLoading();
            showError('Failed to load jobs. Please try again.');
        }
    } finally {
        Dashboard.isLoading = false;
        setTimeout(hideLoadingProgress, 500);
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

let currentSkeleton = null;

async function showSkeletonLoading() {
    const grid = document.getElementById('jobsGrid');
    if (!grid) return;

    // Destroy any existing skeleton
    if (currentSkeleton) {
        currentSkeleton.destroy();
        currentSkeleton = null;
    }

    // Use the grid itself as the container (no wrapper div)
    // This ensures skeleton cards are direct children of the grid
    currentSkeleton = await AnimatedLoadingSkeleton.showWithMinimumTime(
        'jobsGrid',  // Use jobsGrid directly, not a wrapper
        {
            numCards: 6,
            shimmerSpeed: 1.5,
            searchIconColor: '#73daa9'
        },
        1000 // Minimum 1 second display time
    );
}

function hideSkeletonLoading() {
    if (currentSkeleton) {
        currentSkeleton.destroy();
        currentSkeleton = null;
    }
    
    const grid = document.getElementById('jobsGrid');
    if (grid) {
        grid.innerHTML = '';
    }
}

function renderJobs() {
    const grid = document.getElementById('jobsGrid');
    if (!grid) return;

    console.log('=== RENDER JOBS CALLED ===');
    console.log('Total jobs:', Dashboard.jobs.length);
    if (Dashboard.jobs.length > 0) {
        console.log('First job:', Dashboard.jobs[0]);
        console.log('First job keys:', Object.keys(Dashboard.jobs[0]));
        console.log('First job company_logo value:', Dashboard.jobs[0].company_logo);
    }

    if (!Dashboard.jobs || Dashboard.jobs.length === 0) {
        grid.innerHTML = `
            <div class="error-state" style="grid-column: 1 / -1;">
                <div class="error-icon">📭</div>
                <h2>No Jobs Found</h2>
                <p>Try adjusting your search or filters</p>
                <button class="btn btn-primary" onclick="clearAllFilters()">Clear Filters</button>
            </div>
        `;
        return;
    }

    // Render with staggered animation
    grid.innerHTML = Dashboard.jobs.map((job, index) => createJobCard(job, index)).join('');
    
    // Observe cards for lazy animation
    const cards = grid.querySelectorAll('.job-card');
    cards.forEach(card => Dashboard.observer?.observe(card));
}

function createJobCard(job, index = 0) {
    const title = Utils.escapeHtml(job.job_title || 'Position');
    const company = Utils.escapeHtml(job.company || 'Company');
    const location = Utils.escapeHtml(job.location || 'Location');
    const type = Utils.escapeHtml(job.employment_type || 'Full-time');
    
    // Use posted_at_timestamp for DYNAMIC time display
    const posted = Utils.formatRelativeTime(job.posted_date, job.posted_at_timestamp);
    const isNew = isNewJob(job.posted_at_timestamp || job.posted_date);
    
    // Debug: Log the entire job object for first job
    if (index === 0) {
        console.log('=== FIRST JOB OBJECT ===', job);
        console.log('company_logo field:', job.company_logo);
        console.log('Type:', typeof job.company_logo);
    }
    
    // Get logo URL - API returns it as 'company_logo'
    const logoUrl = job.company_logo || '';
    
    // Debug logging for first few jobs
    if (index < 3) {
        console.log(`Job ${index}: ${title} | Company: ${company} | Logo URL:`, logoUrl, '| Length:', logoUrl ? logoUrl.length : 0);
    }

    // Encode job ID properly for URL
    const jobId = encodeURIComponent(job.id || job.linkedin_url);

    // First job is featured (spans 2 columns)
    const isFeatured = index === 0;

    if (isFeatured) {
        // Featured card layout (lg:col-span-2)
        return `
            <div class="group relative p-8 rounded-3xl bg-surface-container-high inner-glow transition-all hover:translate-y-[-4px] duration-300 lg:col-span-2" onclick="navigateToJob('${jobId}')">
                <div class="flex flex-col md:flex-row justify-between items-start gap-6">
                    <div class="flex items-start gap-6 flex-1">
                        <div class="flex-shrink-0 w-16 h-16 rounded-xl bg-surface-container-low flex items-center justify-center overflow-hidden border-2 border-outline-variant/30">
                            ${logoUrl ? `
                            <img src="${Utils.escapeHtml(logoUrl)}" alt="${company}" class="w-14 h-14 object-contain" onload="console.log('Logo loaded:', '${logoUrl}')" onerror="console.log('Logo failed:', '${logoUrl}'); this.parentElement.innerHTML='<div class=\\'w-14 h-14 rounded bg-primary/5 flex items-center justify-center text-primary/20 text-xs font-bold\\'>${company.charAt(0).toUpperCase()}</div>';">
                            ` : `<div class="w-14 h-14 rounded bg-primary/5 flex items-center justify-center text-primary/20 text-xs font-bold">${company.charAt(0).toUpperCase()}</div>`}
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center gap-3 mb-4">
                                <span class="px-3 py-1 bg-primary/20 text-primary text-[10px] font-bold uppercase tracking-widest rounded-full">Featured</span>
                                <span class="text-outline text-xs">${posted}</span>
                            </div>
                            <h3 class="text-3xl font-bold font-headline mb-2 group-hover:text-primary transition-colors">${title}</h3>
                            <p class="text-on-surface-variant text-lg mb-6">${company}</p>
                            <div class="flex flex-wrap gap-6 text-sm text-on-surface/80">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-primary text-base">location_on</span>
                                    ${location}
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-primary text-base">schedule</span>
                                    ${type}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="w-full md:w-auto flex flex-col gap-4">
                        <button class="w-full bg-primary-container text-on-primary-container py-3 px-6 rounded-xl font-bold hover:bg-primary transition-colors" onclick="event.stopPropagation(); navigateToJob('${jobId}')">
                            View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Standard card layout
        return `
            <div class="group p-6 rounded-3xl bg-surface-container inner-glow transition-all hover:translate-y-[-4px] duration-300" onclick="navigateToJob('${jobId}')">
                <div class="mb-6">
                    <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-14 h-14 rounded-lg bg-surface-container-low flex items-center justify-center overflow-hidden border-2 border-outline-variant/30">
                            ${logoUrl ? `
                            <img src="${Utils.escapeHtml(logoUrl)}" alt="${company}" class="w-12 h-12 object-contain" onload="console.log('Logo loaded:', '${logoUrl}')" onerror="console.log('Logo failed:', '${logoUrl}'); this.parentElement.innerHTML='<div class=\\'w-12 h-12 rounded bg-primary/5 flex items-center justify-center text-primary/20 text-xs font-bold\\'>${company.charAt(0).toUpperCase()}</div>';">
                            ` : `<div class="w-12 h-12 rounded bg-primary/5 flex items-center justify-center text-primary/20 text-xs font-bold">${company.charAt(0).toUpperCase()}</div>`}
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-3">
                                <span class="text-outline text-xs">${type}</span>
                                <span class="w-1 h-1 bg-outline rounded-full"></span>
                                <span class="text-outline text-xs">${posted}</span>
                            </div>
                            <h3 class="text-xl font-bold font-headline mb-1 group-hover:text-primary transition-colors">${title}</h3>
                            <p class="text-on-surface-variant text-sm mb-4">${company}</p>
                        </div>
                    </div>
                </div>
                <div class="space-y-3 mb-8">
                    <div class="flex items-center gap-2 text-sm text-on-surface/60">
                        <span class="material-symbols-outlined text-xs">location_on</span>
                        ${location}
                    </div>
                </div>
                <div class="flex items-center justify-between mt-auto">
                    <button class="w-full py-3 rounded-xl border border-primary/20 text-primary font-semibold group-hover:bg-primary-container group-hover:text-on-primary-container transition-all" onclick="event.stopPropagation(); navigateToJob('${jobId}')">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }
}

function isNewJob(postedDate) {
    if (!postedDate) return false;
    
    const now = new Date();
    const posted = new Date(postedDate);
    const hoursDiff = (now - posted) / (1000 * 60 * 60);
    
    return hoursDiff < 24;
}

function renderPagination() {
    const container = document.getElementById('footerPagination');

    if (!container) return;

    if (Dashboard.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    // Use the actual jobs array length, not stats
    const actualJobCount = Dashboard.jobs.length > 0 ? 
        (Dashboard.stats?.total_jobs || Dashboard.jobs.length) : 0;

    // Build pagination HTML with shadcn/ui design
    let html = `
        <div class="pagination-header">
            <h2>Explore Opportunities</h2>
            <p>Browse through ${actualJobCount.toLocaleString()} curated positions</p>
        </div>

        <nav class="pagination-nav" aria-label="Pagination navigation">
            <ul class="pagination-content">
    `;

    // Previous button
    html += `
        <li class="pagination-item">
            <button class="pagination-nav-btn prev" 
                    onclick="goToPage(${Dashboard.currentPage - 1})"
                    ${Dashboard.currentPage === 1 ? 'disabled' : ''}
                    aria-label="Go to previous page">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m15 18-6-6 6-6"/>
                </svg>
                Previous
            </button>
        </li>
    `;

    // Page numbers
    const maxVisible = 7;
    let startPage = Math.max(1, Dashboard.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(Dashboard.totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    // First page + ellipsis
    if (startPage > 1) {
        html += `
            <li class="pagination-item">
                <button class="pagination-btn" onclick="goToPage(1)" aria-label="Go to page 1">1</button>
            </li>
        `;
        if (startPage > 2) {
            html += `
                <li class="pagination-item">
                    <span class="pagination-ellipsis" aria-hidden="true">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="1"/>
                            <circle cx="19" cy="12" r="1"/>
                            <circle cx="5" cy="12" r="1"/>
                        </svg>
                    </span>
                </li>
            `;
        }
    }

    // Page buttons
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="pagination-item">
                <button class="pagination-btn ${i === Dashboard.currentPage ? 'active' : ''}"
                        onclick="goToPage(${i})"
                        aria-label="Go to page ${i}"
                        ${i === Dashboard.currentPage ? 'aria-current="page"' : ''}>
                    ${i}
                </button>
            </li>
        `;
    }

    // Last page + ellipsis
    if (endPage < Dashboard.totalPages) {
        if (endPage < Dashboard.totalPages - 1) {
            html += `
                <li class="pagination-item">
                    <span class="pagination-ellipsis" aria-hidden="true">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="1"/>
                            <circle cx="19" cy="12" r="1"/>
                            <circle cx="5" cy="12" r="1"/>
                        </svg>
                    </span>
                </li>
            `;
        }
        html += `
            <li class="pagination-item">
                <button class="pagination-btn" onclick="goToPage(${Dashboard.totalPages})" aria-label="Go to page ${Dashboard.totalPages}">${Dashboard.totalPages}</button>
            </li>
        `;
    }

    // Next button
    html += `
        <li class="pagination-item">
            <button class="pagination-nav-btn next" 
                    onclick="goToPage(${Dashboard.currentPage + 1})"
                    ${Dashboard.currentPage === Dashboard.totalPages ? 'disabled' : ''}
                    aria-label="Go to next page">
                Next
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m9 18 6-6-6-6"/>
                </svg>
            </button>
        </li>
    `;

    html += `
            </ul>
        </nav>

        <div class="pagination-info">
            <span class="pagination-info-text">
                Page <span>${Dashboard.currentPage}</span> of <span>${Dashboard.totalPages}</span>
            </span>
        </div>
    `;

    container.innerHTML = html;
}

function renderStats() {
    if (!Dashboard.stats) return;

    const { total_jobs, cities, companies, last_updated } = Dashboard.stats;

    // Animate stat numbers
    animateValue('totalJobs', 0, total_jobs || 0, 500);
    const totalCitiesEl = document.getElementById('totalCities');
    if (totalCitiesEl) totalCitiesEl.textContent = Object.keys(cities || {}).length;
    const totalCompaniesEl = document.getElementById('totalCompanies');
    if (totalCompaniesEl) totalCompaniesEl.textContent = Object.keys(companies || {}).length;

    if (last_updated) {
        const lastUpdatedEl = document.getElementById('lastUpdated');
        if (lastUpdatedEl) lastUpdatedEl.textContent = Utils.formatDate(last_updated);
    }
    
    // Update footer pagination count to match stats
    updateFooterJobCount(total_jobs || 0);
}

function updateFooterJobCount(count) {
    const headerEl = document.querySelector('#footerPagination .pagination-header p');
    if (headerEl) {
        headerEl.textContent = `Browse through ${count.toLocaleString()} curated positions`;
    }
}

function animateValue(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.classList.add('counting');
    
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            element.textContent = end.toLocaleString();
            element.classList.remove('counting');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString();
        }
    }, 16);
}

function populateCityFilter() {
    const select = document.getElementById('cityFilter');
    if (!select) return;
    select.innerHTML = '<option value="">All Cities</option>' +
        Dashboard.cities.map(city => `<option value="${Utils.escapeHtml(city)}">${Utils.escapeHtml(city)} (${Dashboard.cities.filter(c => c === city).length})</option>`).join('');
}

function populateTypeFilter() {
    const select = document.getElementById('typeFilter');
    if (!select) return;
    select.innerHTML = '<option value="">All Types</option>' +
        Dashboard.employmentTypes.map(type => `<option value="${Utils.escapeHtml(type)}">${Utils.escapeHtml(type)}</option>`).join('');
}

function updateResultsCount(total) {
    const element = document.getElementById('resultsCount');
    if (!element) return;
    
    element.classList.add('updating');
    element.textContent = `${total.toLocaleString()} job${total !== 1 ? 's' : ''} found`;
    
    setTimeout(() => {
        element.classList.remove('updating');
    }, 300);
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Initialize combo box filters
    initFilterComboBoxes();

    // Search input with reduced debounce (200ms instead of 500ms)
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.querySelector('.search-clear');

    if (searchClear) {
        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            Dashboard.filters.search = '';
            goToPage(1);
            searchInput.focus();
        });
    }

    if (searchInput) {
        const debouncedSearch = Utils.debounce((e) => {
            Dashboard.filters.search = e.target.value.trim();
            goToPage(1);
        }, 200);
        searchInput.addEventListener('input', debouncedSearch);
    }

    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleManualRefresh);
    }
}

function initFilterComboBoxes() {
    // City combo box
    const cityComboBox = new ComboBox('cityComboBox', {
        placeholder: 'All Cities',
        darkTheme: true,
        onChange: (item) => {
            Dashboard.filters.city = item.value;
            goToPage(1);
        }
    });

    // Type combo box
    const typeComboBox = new ComboBox('typeComboBox', {
        placeholder: 'Job Type',
        darkTheme: true,
        onChange: (item) => {
            Dashboard.filters.type = item.value;
            goToPage(1);
        }
    });

    // Load cities and types from API
    loadFilterOptions(cityComboBox, typeComboBox);
}

async function loadFilterOptions(cityComboBox, typeComboBox) {
    try {
        // Load cities from existing /api/cities endpoint
        const citiesResponse = await fetch('/api/cities');
        const citiesData = await citiesResponse.json();
        if (citiesData.success) {
            // Format as combo box items
            const citiesWithCounts = citiesData.cities.map(city => ({
                value: city,
                label: city,
                secondary: ''
            }));
            cityComboBox.setItems(citiesWithCounts);
        }

        // Load job types from existing /api/employment-types endpoint
        const typesResponse = await fetch('/api/employment-types');
        const typesData = await typesResponse.json();
        if (typesData.success) {
            const typesWithCounts = typesData.types.map(type => ({
                value: type,
                label: type,
                secondary: ''
            }));
            typeComboBox.setItems(typesWithCounts);
        }
    } catch (error) {
        console.error('Failed to load filter options:', error);
    }
}

// ============================================================================
// Navigation & Actions
// ============================================================================

function navigateToJob(jobId) {
    window.location.href = `/job/${jobId}`;
}

function goToPage(page) {
    if (page < 1 || page > Dashboard.totalPages) return;
    Dashboard.currentPage = page;
    
    // Update URL with page number for persistence on refresh
    const url = new URL(window.location);
    url.searchParams.set('page', page);
    window.history.pushState({ page: page }, '', url);
    
    loadJobs(page);

    // Smooth scroll to the TOP of the page (not the job grid)
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function applyFilters() {
    updateFilterChips();
    goToPage(1);
}

function clearAllFilters() {
    Dashboard.filters = { search: '', city: '', type: '' };
    document.getElementById('searchInput').value = '';
    document.getElementById('cityFilter').value = '';
    document.getElementById('typeFilter').value = '';
    updateFilterChips();
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
    if (!indicator) return;
    
    indicator.classList.add('refreshing');
    indicator.innerHTML = '<span class="pulse"></span><span>New jobs available! Refreshing...</span>';

    setTimeout(() => {
        indicator.classList.remove('refreshing');
        indicator.innerHTML = '<span class="pulse"></span><span>Auto-refresh in <span id="refreshCountdown">60</span>s</span>';
        loadJobs(Dashboard.currentPage);
        loadStats();
    }, 2000);
}

// ============================================================================
// UI Helpers
// ============================================================================

function showError(message) {
    const grid = document.getElementById('jobsGrid');
    if (!grid) return;
    
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
// Additional Features
// ============================================================================

// Scroll to Top Button
function setupScrollToTop() {
    const scrollBtn = document.createElement('button');
    scrollBtn.className = 'scroll-to-top';
    scrollBtn.setAttribute('aria-label', 'Scroll to top');
    scrollBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 15l-6-6-6 6"/>
        </svg>
    `;
    document.body.appendChild(scrollBtn);

    const handleScroll = Utils.debounce(() => {
        if (window.scrollY > 500) {
            scrollBtn.classList.add('visible');
        } else {
            scrollBtn.classList.remove('visible');
        }
    }, 10);

    window.addEventListener('scroll', handleScroll, { passive: true });
    
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Initialize scroll to top on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupScrollToTop);
} else {
    setupScrollToTop();
}

// Filter Chips Display
function updateFilterChips() {
    const container = document.querySelector('.filter-chips');
    if (!container) return;
    
    const activeFilters = [];
    
    if (Dashboard.filters.search) {
        activeFilters.push({ type: 'search', label: `Search: "${Dashboard.filters.search}"` });
    }
    if (Dashboard.filters.city) {
        activeFilters.push({ type: 'city', label: Dashboard.filters.city });
    }
    if (Dashboard.filters.type) {
        activeFilters.push({ type: 'type', label: Dashboard.filters.type });
    }
    
    if (activeFilters.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = activeFilters.map(filter => `
        <span class="filter-chip">
            ${filter.label}
            <button class="filter-chip-remove" onclick="removeFilter('${filter.type}')" aria-label="Remove ${filter.type} filter">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </span>
    `).join('');
}

function removeFilter(type) {
    if (type === 'search') {
        Dashboard.filters.search = '';
        document.getElementById('searchInput').value = '';
    } else if (type === 'city') {
        Dashboard.filters.city = '';
        document.getElementById('cityFilter').value = '';
    } else if (type === 'type') {
        Dashboard.filters.type = '';
        document.getElementById('typeFilter').value = '';
    }
    goToPage(1);
}

window.removeFilter = removeFilter;

// Loading Progress Bar
function showLoadingProgress() {
    let progressEl = document.querySelector('.loading-progress');
    if (!progressEl) {
        progressEl = document.createElement('div');
        progressEl.className = 'loading-progress';
        progressEl.innerHTML = '<div class="loading-progress-bar"></div>';
        document.body.insertBefore(progressEl, document.body.firstChild);
    }
    progressEl.classList.add('active');
}

function hideLoadingProgress() {
    const progressEl = document.querySelector('.loading-progress');
    if (progressEl) {
        progressEl.classList.remove('active');
    }
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
window.removeFilter = removeFilter;
