/**
 * RoleBoard — Tech & Non-Tech Jobs Dashboard
 * Main dashboard logic with SayBriefly design
 */
const RoleBoard = {
    // State
    currentPage: 1,
    totalPages: 1,
    limit: 30,
    filters: { domains: [], search: '', location: '', level: '' },
    jobs: [],
    stats: null,
    locations: [],

    // Loading
    isLoading: false,

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            // Load initial data
            await Promise.all([
                this.loadStats(),
                this.loadLocations(),
                this.loadDomains(),
                this.loadJobs(1)
            ]);

            // Setup event listeners
            this.setupEventListeners();

            console.log('✅ RoleBoard initialized');
        } catch (error) {
            console.error('❌ RoleBoard init failed:', error);
            this.showError('Failed to load jobs. Please try again.');
        }
    },

    // ========================================================================
    // Data Loading
    // ========================================================================

    async loadJobs(page = 1) {
        if (this.isLoading) return;
        this.isLoading = true;
        this.showSkeleton();

        try {
            const params = { page, limit: this.limit };
            if (this.filters.domains && this.filters.domains.length) {
                params.domains = this.filters.domains.join(',');
            }
            if (this.filters.search) {
                params.search = this.filters.search;
            }
            if (this.filters.location) {
                params.location = this.filters.location;
            }
            if (this.filters.level) {
                params.level = this.filters.level;
            }

            const response = await API.getJobs(page, this.limit, {
                domains: this.filters.domains.length ? this.filters.domains.join(',') : '',
                search: this.filters.search,
                location: this.filters.location,
                level: this.filters.level
            });

            if (response.success) {
                this.jobs = response.jobs || [];
                this.currentPage = response.pagination?.page || page;
                this.totalPages = response.pagination?.total_pages || 1;

                this.hideSkeleton();
                this.renderJobs();
                this.renderPagination();
                this.updateResultsCount(response.pagination?.total || 0);

                // Update stats total from API
                if (this.stats) {
                    this.stats.total_jobs = response.pagination?.total || 0;
                    this.renderStats();
                }
            }
        } catch (error) {
            console.error('Error loading jobs:', error);
            if (this.jobs.length === 0) {
                this.hideSkeleton();
                this.showError('Failed to load jobs. Please try again.');
            }
        } finally {
            this.isLoading = false;
        }
    },

    async loadStats() {
        try {
            const response = await API.getStats();
            if (response.success) {
                this.stats = response.stats;
                this.renderStats();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    },

    async loadLocations() {
        try {
            const response = await API.getLocations();
            if (response.success && response.locations) {
                this.locations = response.locations;
                this.populateLocationFilter();
            }
        } catch (error) {
            console.error('Error loading locations:', error);
        }
    },

    async loadDomains() {
        try {
            const response = await API.getDomains();
            if (response.success && response.domains) {
                this.domains = response.domains;
                this.renderDomainFilter();
            }
        } catch (error) {
            console.error('Error loading domains:', error);
        }
    },

    renderDomainFilter() {
        const select = document.getElementById('domainFilter');
        if (!select || !this.domains || !this.domains.length) return;

        select.innerHTML = this.domains.map(domain => {
            const value = domain === 'All' ? 'All' : domain;
            return `<option value="${Utils.escapeHtml(value)}" ${domain === 'All' ? 'selected' : ''}>${Utils.escapeHtml(domain)}</option>`;
        }).join('');
    },

    populateLocationFilter() {
        const select = document.getElementById('locationFilter');
        if (!select) return;
        
        select.innerHTML = '<option value="">All Locations</option>' +
            this.locations.map(loc => 
                `<option value="${Utils.escapeHtml(loc)}">${Utils.escapeHtml(loc)}</option>`
            ).join('');
    },

    // ========================================================================
    // Rendering
    // ========================================================================

    showSkeleton() {
        const grid = document.getElementById('jobsGrid');
        if (!grid) return;
        grid.innerHTML = Array(6).fill('<div class="skeleton-card"></div>').join('');
    },

    hideSkeleton() {
        const grid = document.getElementById('jobsGrid');
        if (grid) grid.innerHTML = '';
    },

    renderJobs() {
        const grid = document.getElementById('jobsGrid');
        if (!grid) return;

        if (!this.jobs || this.jobs.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 80px 24px;">
                    <p style="font-size: 48px; margin-bottom: 16px;">📭</p>
                    <h2 style="font-family: var(--font-inter); font-weight: 600; font-size: 20px; margin-bottom: 8px;">No roles found</h2>
                    <p style="color: var(--color-pencil-gray); font-size: 14px;">Try a different filter or check back later</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.jobs.map((job, index) => this.createJobCard(job, index)).join('');
    },

    createJobCard(job, index) {
        // Sanitize domain for use as CSS class name (any non-alphanumeric run -> single dash)
        const safeDomain = (job.domain || 'Other').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase();
        const title = Utils.escapeHtml(job.role || 'Position');
        const company = Utils.escapeHtml(job.company || 'Company');
        const location = Utils.escapeHtml(job.location || 'India');
        const domain = job.domain || 'Other';
        const domainClass = Utils.getDomainClass(domain);
        const level = job.level || '';
        const levelClass = Utils.getLevelClass(level);
        const levelIcon = level === 'Entry Level' ? '🟢' : level === 'Mid Level' ? '🟡' : level === 'Senior Level' ? '🔴' : '';
        const dateStr = Utils.formatDate(job.date_added);
        const url = job.url || '#';
        const animDelay = (index * 50);

        return `
            <div class="job-card domain-${safeDomain}"
                 style="animation: cardFadeIn 0.4s ease ${animDelay}ms both;"
                 onclick="RoleBoard.openJob('${Utils.escapeHtml(url)}')">
                <div class="job-card-header">
                    <span class="job-domain-badge ${domainClass}">${Utils.escapeHtml(domain)}</span>
                    <div class="job-card-header-right">
                        ${level ? `<span class="job-level-badge ${levelClass}">${levelIcon} ${Utils.escapeHtml(level.replace(' Level', ''))}</span>` : ''}
                        <span class="job-date">${dateStr}</span>
                    </div>
                </div>
                <div class="job-company">${company}</div>
                <div class="job-title">${title}</div>
                <div class="job-card-footer">
                    <span class="job-location">
                        <span class="material-symbols-outlined">location_on</span>
                        ${location}
                    </span>
                    <span class="job-card-arrow">→</span>
                </div>
            </div>
        `;
    },

    renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;

        if (this.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '';

        // Previous
        html += `
            <button class="pagination-btn" onclick="RoleBoard.goToPage(${this.currentPage - 1})"
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                ←
            </button>
        `;

        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);
        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}"
                        onclick="RoleBoard.goToPage(${i})">${i}</button>
            `;
        }

        // Next
        html += `
            <button class="pagination-btn" onclick="RoleBoard.goToPage(${this.currentPage + 1})"
                    ${this.currentPage === this.totalPages ? 'disabled' : ''}>
                →
            </button>
        `;

        container.innerHTML = html;
    },

    renderStats() {
        if (!this.stats) return;

        const totalJobs = document.getElementById('totalJobs');
        const totalDomains = document.getElementById('totalDomains');
        const totalCompanies = document.getElementById('totalCompanies');

        if (totalJobs) totalJobs.textContent = (this.stats.total_jobs || 0).toLocaleString();
        if (totalDomains) totalDomains.textContent = Object.keys(this.stats.domains || {}).length;
        if (totalCompanies) totalCompanies.textContent = (this.stats.total_companies || 0).toLocaleString();
    },

    updateResultsCount(total) {
        const el = document.getElementById('resultsCount');
        if (el) {
            el.textContent = `${total.toLocaleString()} role${total !== 1 ? 's' : ''} found`;
        }
    },

    // ========================================================================
    // Event Listeners
    // ========================================================================

    setupEventListeners() {
        // Role tag filter (native multi-select, same pattern as location/level)
        const domainFilter = document.getElementById('domainFilter');
        if (domainFilter) {
            domainFilter.addEventListener('change', () => {
                const allOption = domainFilter.querySelector('option[value="All"]');
                const selected = [...domainFilter.selectedOptions].map(o => o.value);

                if (selected.includes('All') && selected.length > 1) {
                    // A specific tag was picked while "All" was on → "All" loses
                    if (allOption) allOption.selected = false;
                    this.filters.domains = selected.filter(v => v !== 'All' && v !== '');
                } else if (selected.includes('All') || selected.length === 0) {
                    // "All Domains" (or nothing selected) → show everything
                    if (allOption && selected.length === 0) allOption.selected = true;
                    this.filters.domains = [];
                } else {
                    // One or more specific tags selected
                    this.filters.domains = selected.filter(v => v !== 'All' && v !== '');
                }

                this.goToPage(1);
            });
        }

        // Search with debounce
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const debouncedSearch = Utils.debounce((query) => {
                this.filters.search = query;
                this.goToPage(1);
            }, 200);

            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                if (query.length >= 2 || query.length === 0) {
                    debouncedSearch(query);
                }
            });
        }

        // Location filter
        const locationFilter = document.getElementById('locationFilter');
        if (locationFilter) {
            locationFilter.addEventListener('change', (e) => {
                this.filters.location = e.target.value;
                this.goToPage(1);
            });
        }

        // Experience Level filter
        const levelFilter = document.getElementById('levelFilter');
        if (levelFilter) {
            levelFilter.addEventListener('change', (e) => {
                this.filters.level = e.target.value;
                this.goToPage(1);
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.handleRefresh());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;

            if (e.key === '/') {
                e.preventDefault();
                searchInput?.focus();
            }
            if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
                e.preventDefault();
                this.handleRefresh();
            }
            if (e.key === 'ArrowRight') {
                this.goToPage(this.currentPage + 1);
            }
            if (e.key === 'ArrowLeft') {
                this.goToPage(this.currentPage - 1);
            }
        });
    },

    // ========================================================================
    // Actions
    // ========================================================================

    openJob(url) {
        if (url && url !== '#' && url !== '') {
            window.open(url, '_blank');
        }
    },

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadJobs(page);
    },

    async handleRefresh() {
        try {
            await API.refreshData();
            await Promise.all([
                this.loadStats(),
                this.loadJobs(this.currentPage)
            ]);
        } catch (error) {
            console.error('Refresh failed:', error);
        }
    },

    showError(message) {
        const grid = document.getElementById('jobsGrid');
        if (!grid) return;
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 80px 24px;">
                <p style="font-size: 48px; margin-bottom: 16px;">❌</p>
                <h2 style="font-family: var(--font-inter); font-weight: 600; font-size: 20px; margin-bottom: 8px;">Something went wrong</h2>
                <p style="color: var(--color-pencil-gray); font-size: 14px; margin-bottom: 24px;">${Utils.escapeHtml(message)}</p>
                <button onclick="RoleBoard.init()" style="padding: 8px 24px; background: var(--color-forest-ink); color: var(--color-cream-paper); border: none; border-radius: 6px; cursor: pointer; font-family: var(--font-inter); font-size: 14px;">
                    Try Again
                </button>
            </div>
        `;
    }
};

// Expose globally
window.RoleBoard = RoleBoard;
