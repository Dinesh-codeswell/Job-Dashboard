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
    domains: [],
    viewMode: 'feed', // 'feed' | 'pipeline'
    pipeline: {},

    // Loading & Request tracking
    isLoading: false,
    currentRequestId: 0,

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            // Initialize local-first application pipeline
            this.initPipeline();

            // Setup event listeners immediately so user interactions are never blocked
            this.setupEventListeners();

            // Load jobs immediately (highest visual priority for real-time responsiveness)
            this.loadJobs(1);

            // Concurrently fetch domains, locations, and stats in background
            this.loadDomains();
            this.loadLocations();
            this.loadStats();

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
        const requestId = ++this.currentRequestId;
        this.isLoading = true;

        const grid = document.getElementById('jobsGrid');
        // If no jobs exist yet, display skeleton cards.
        // If jobs are already rendered, gently dim them without jarring DOM wipe.
        if (!this.jobs || this.jobs.length === 0) {
            this.showSkeleton();
        } else if (grid) {
            grid.classList.add('loading-fade');
        }

        try {
            const response = await API.getJobs(page, this.limit, {
                domains: this.filters.domains.length ? this.filters.domains.join(',') : '',
                search: this.filters.search,
                location: this.filters.location,
                level: this.filters.level
            });

            // If user performed another action while this request was in flight, ignore stale response
            if (requestId !== this.currentRequestId) {
                return;
            }

            if (response.success) {
                this.jobs = response.jobs || [];
                this.currentPage = response.pagination?.page || page;
                this.totalPages = response.pagination?.total_pages || 1;

                this.hideSkeleton();
                this.renderJobs();
                this.renderPagination();
                this.updateResultsCount(response.pagination?.total || 0);

                // Update stats total from API
                if (this.stats && response.pagination?.total !== undefined) {
                    this.stats.total_jobs = response.pagination.total;
                    this.renderStats();
                }
            }
        } catch (error) {
            if (requestId === this.currentRequestId) {
                console.error('Error loading jobs:', error);
                if (this.jobs.length === 0) {
                    this.hideSkeleton();
                    this.showError('Failed to load jobs. Please try again.');
                }
            }
        } finally {
            if (requestId === this.currentRequestId) {
                this.isLoading = false;
                if (grid) grid.classList.remove('loading-fade');
            }
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
        const menu = document.getElementById('domainFilterMenu');
        if (!menu || !this.domains || !this.domains.length) return;

        menu.innerHTML = this.domains.map(domain => {
            const isAll = domain === 'All';
            return `
                <label class="domain-filter-option">
                    <input type="checkbox" class="domain-filter-checkbox" data-domain="${Utils.escapeHtml(domain)}" ${isAll ? 'checked' : ''} />
                    <span class="domain-filter-option-label">${Utils.escapeHtml(domain)}</span>
                </label>
            `;
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
                <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 56px 24px; background: var(--color-frost-white); border: 2px solid var(--color-charcoal-ink); border-radius: var(--radius-cards); box-shadow: var(--shadow-card);">
                    <p style="font-size: 40px; margin-bottom: 12px; line-height: 1;">🦆</p>
                    <h2 style="font-family: var(--font-aeonik-mono); font-weight: 700; font-size: 18px; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.04em;">// NO ROLES FOUND</h2>
                    <p style="color: var(--color-graphite); font-family: var(--font-aeonik-mono); font-size: 13px; letter-spacing: 0.02em;">Configure Notion database or refine your active search and filters.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.jobs.map((job, index) => this.createJobCard(job, index)).join('');
    },

    createJobCard(job, index) {
        const jobId = this.getJobId(job);
        const pipelineItem = this.pipeline[jobId];

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

        let pipelineActionHtml = '';
        if (pipelineItem) {
            pipelineActionHtml = `
                <div class="card-pipeline-status" onclick="event.stopPropagation();">
                    <select class="card-status-select status-${pipelineItem.status}" onchange="RoleBoard.updatePipelineStatus('${Utils.escapeHtml(jobId)}', this.value)">
                        <option value="saved" ${pipelineItem.status === 'saved' ? 'selected' : ''}>📌 SAVED</option>
                        <option value="applied" ${pipelineItem.status === 'applied' ? 'selected' : ''}>📤 APPLIED</option>
                        <option value="interviewing" ${pipelineItem.status === 'interviewing' ? 'selected' : ''}>🎤 INTERVIEWING</option>
                        <option value="offered" ${pipelineItem.status === 'offered' ? 'selected' : ''}>🎉 OFFERED</option>
                        <option value="rejected" ${pipelineItem.status === 'rejected' ? 'selected' : ''}>⛔ REJECTED</option>
                        <option value="__remove__">✕ Remove</option>
                    </select>
                </div>
            `;
        } else {
            pipelineActionHtml = `
                <button type="button" class="btn-card-track" onclick="event.stopPropagation(); RoleBoard.trackJobFromCard('${Utils.escapeHtml(jobId)}')" title="Track in Application Pipeline">
                    <span class="material-symbols-outlined" style="font-size: 13px;">bookmark_add</span>
                    <span>+ TRACK</span>
                </button>
            `;
        }

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
                    <div class="job-card-footer-actions">
                        ${pipelineActionHtml}
                        <span class="job-card-arrow">→</span>
                    </div>
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
        // Role tag filter — dropdown multi-select (open/collapse like other filters)
        const trigger = document.getElementById('domainFilterTrigger');
        const menu = document.getElementById('domainFilterMenu');

        if (trigger && menu) {
            // Open / close on trigger click
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = menu.classList.toggle('open');
                trigger.classList.toggle('open', isOpen);
                trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });

            // Collapse when clicking outside the dropdown
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.domain-filter-wrapper')) {
                    menu.classList.remove('open');
                    trigger.classList.remove('open');
                    trigger.setAttribute('aria-expanded', 'false');
                }
            });

            // Collapse on Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    menu.classList.remove('open');
                    trigger.classList.remove('open');
                    trigger.setAttribute('aria-expanded', 'false');
                }
            });

            // Tag selection — menu stays open while picking (multi-select)
            menu.addEventListener('change', (e) => {
                if (!e.target.classList.contains('domain-filter-checkbox')) return;

                const cb = e.target;
                const allBox = menu.querySelector('.domain-filter-checkbox[data-domain="All"]');
                const specificBoxes = [...menu.querySelectorAll('.domain-filter-checkbox:not([data-domain="All"])')];

                if (cb.dataset.domain === 'All' && cb.checked) {
                    // "All Domains" clears every specific tag
                    specificBoxes.forEach(b => b.checked = false);
                    this.filters.domains = [];
                } else {
                    // Selecting any specific tag unchecks "All Domains"
                    if (allBox) allBox.checked = false;
                    this.filters.domains = specificBoxes
                        .filter(b => b.checked)
                        .map(b => b.dataset.domain);
                }

                this.updateDomainFilterLabel();
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

        // View Mode Switcher
        document.getElementById('tabBrowseFeed')?.addEventListener('click', () => this.switchView('feed'));
        document.getElementById('tabPipeline')?.addEventListener('click', () => this.switchView('pipeline'));

        // Pipeline actions
        document.getElementById('exportPipelineCsvBtn')?.addEventListener('click', () => this.exportPipelineCsv());
        document.getElementById('clearPipelineBtn')?.addEventListener('click', () => this.clearPipeline());

        // Alerts & RSS Feeds Modal
        document.getElementById('alertsModalBtn')?.addEventListener('click', () => this.openAlertsModal());
        document.getElementById('alertsModalClose')?.addEventListener('click', () => this.closeAlertsModal());
        document.getElementById('alertsModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeAlertsModal();
        });
        document.getElementById('copyRssUrlBtn')?.addEventListener('click', () => this.copyRssUrl());
        document.getElementById('testWebhookBtn')?.addEventListener('click', () => this.testWebhook());

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

    updateDomainFilterLabel() {
        const label = document.getElementById('domainFilterLabel');
        if (!label) return;

        if (!this.filters.domains.length) {
            label.textContent = 'All Domains';
        } else if (this.filters.domains.length <= 2) {
            label.textContent = this.filters.domains.join(' + ');
        } else {
            label.textContent = `${this.filters.domains.length} tags selected`;
        }
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
        const btn = document.getElementById('refreshBtn');
        if (btn) btn.classList.add('rotating');
        try {
            API.clearCache();
            await API.refreshData();
            await Promise.all([
                this.loadStats(),
                this.loadLocations(),
                this.loadJobs(this.currentPage)
            ]);
        } catch (error) {
            console.error('Refresh failed:', error);
        } finally {
            if (btn) {
                setTimeout(() => btn.classList.remove('rotating'), 400);
            }
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
    },

    // ========================================================================
    // Pipeline State & Helper Methods
    // ========================================================================

    getJobId(job) {
        if (!job) return 'job_' + Math.random().toString(36).substring(2, 9);
        if (job.id) return String(job.id);
        const comp = (job.company || '').trim().toLowerCase();
        const role = (job.role || '').trim().toLowerCase();
        return `${comp}___${role}`.replace(/[^a-z0-9_-]/g, '_');
    },

    initPipeline() {
        try {
            const raw = localStorage.getItem('roleboard_pipeline_v1');
            this.pipeline = raw ? JSON.parse(raw) : {};
        } catch (e) {
            console.warn('Failed to parse saved pipeline from localStorage:', e);
            this.pipeline = {};
        }
        this.updatePipelineBadges();
    },

    savePipeline(shouldUpdateBadges = true) {
        try {
            localStorage.setItem('roleboard_pipeline_v1', JSON.stringify(this.pipeline));
        } catch (e) {
            console.error('Failed to save pipeline to localStorage:', e);
        }
        if (shouldUpdateBadges) {
            this.updatePipelineBadges();
        }
    },

    updatePipelineBadges() {
        const items = Object.values(this.pipeline);
        const totalBadge = document.getElementById('pipelineTabBadge');
        if (totalBadge) totalBadge.textContent = items.length;

        const counts = { saved: 0, applied: 0, interviewing: 0, offered: 0, rejected: 0 };
        items.forEach(item => {
            if (counts[item.status] !== undefined) counts[item.status]++;
        });

        ['saved', 'applied', 'interviewing', 'offered', 'rejected'].forEach(status => {
            const el = document.getElementById(`count-${status}`);
            if (el) el.textContent = counts[status];
        });
    },

    trackJobFromCard(jobId) {
        const job = this.jobs.find(j => this.getJobId(j) === jobId);
        if (!job) return;
        this.pipeline[jobId] = {
            id: jobId,
            role: job.role || 'Position',
            company: job.company || 'Company',
            location: job.location || 'India',
            domain: job.domain || 'Other',
            level: job.level || '',
            url: job.url || '#',
            status: 'saved',
            notes: '',
            dateAdded: new Date().toISOString()
        };
        this.savePipeline();
        this.renderJobs();
    },

    updatePipelineStatus(jobId, newStatus) {
        if (newStatus === '__remove__') {
            this.removeFromPipeline(jobId);
            return;
        }
        if (this.pipeline[jobId]) {
            this.pipeline[jobId].status = newStatus;
            this.pipeline[jobId].dateUpdated = new Date().toISOString();
            this.savePipeline();
            if (this.viewMode === 'feed') {
                this.renderJobs();
            } else {
                this.renderKanban();
            }
        }
    },

    updatePipelineNotes(jobId, notes) {
        if (this.pipeline[jobId]) {
            this.pipeline[jobId].notes = notes;
            this.savePipeline(false);
        }
    },

    removeFromPipeline(jobId) {
        if (this.pipeline[jobId]) {
            delete this.pipeline[jobId];
            this.savePipeline();
            if (this.viewMode === 'feed') {
                this.renderJobs();
            } else {
                this.renderKanban();
            }
        }
    },

    clearPipeline() {
        if (Object.keys(this.pipeline).length === 0) return;
        if (confirm('Are you sure you want to clear all tracked applications in your pipeline?')) {
            this.pipeline = {};
            this.savePipeline();
            if (this.viewMode === 'feed') this.renderJobs();
            else this.renderKanban();
        }
    },

    exportPipelineCsv() {
        const items = Object.values(this.pipeline);
        if (items.length === 0) {
            alert('Your pipeline is currently empty. Track some jobs first!');
            return;
        }

        const headers = ['Role', 'Company', 'Location', 'Domain', 'Level', 'Status', 'Date Added', 'Notes', 'URL'];
        const escapeCsv = (val) => {
            const str = String(val || '').replace(/"/g, '""');
            return `"${str}"`;
        };

        const rows = items.map(item => [
            escapeCsv(item.role),
            escapeCsv(item.company),
            escapeCsv(item.location),
            escapeCsv(item.domain),
            escapeCsv(item.level),
            escapeCsv(item.status),
            escapeCsv(item.dateAdded),
            escapeCsv(item.notes),
            escapeCsv(item.url)
        ].join(','));

        const csvContent = 'data:text/csv;charset=utf-8,' + encodeURIComponent([headers.join(','), ...rows].join('\n'));
        const link = document.createElement('a');
        link.setAttribute('href', csvContent);
        link.setAttribute('download', `job_applications_pipeline_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    renderKanban() {
        const columns = {
            saved: document.getElementById('list-saved'),
            applied: document.getElementById('list-applied'),
            interviewing: document.getElementById('list-interviewing'),
            offered: document.getElementById('list-offered'),
            rejected: document.getElementById('list-rejected')
        };

        Object.values(columns).forEach(col => { if (col) col.innerHTML = ''; });

        const items = Object.values(this.pipeline);
        const grouped = { saved: [], applied: [], interviewing: [], offered: [], rejected: [] };
        items.forEach(item => {
            if (grouped[item.status]) grouped[item.status].push(item);
        });

        Object.keys(grouped).forEach(status => {
            const colList = columns[status];
            if (!colList) return;

            const list = grouped[status];
            if (list.length === 0) {
                colList.innerHTML = `<div class="kanban-empty-slot"><span>No roles here yet</span></div>`;
                return;
            }

            colList.innerHTML = list.map(item => {
                const safeDomain = (item.domain || 'Other').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase();
                const domainClass = Utils.getDomainClass(item.domain || 'Other');
                const dateStr = Utils.formatDate(item.dateAdded);

                return `
                    <div class="kanban-card domain-${safeDomain}">
                        <div class="kanban-card-top">
                            <span class="job-domain-badge ${domainClass}">${Utils.escapeHtml(item.domain || 'Other')}</span>
                            <span class="kanban-card-date">${dateStr}</span>
                        </div>
                        <div class="kanban-card-company">${Utils.escapeHtml(item.company)}</div>
                        <div class="kanban-card-title">${Utils.escapeHtml(item.role)}</div>
                        <div class="kanban-card-location">
                            <span class="material-symbols-outlined" style="font-size: 13px;">location_on</span>
                            ${Utils.escapeHtml(item.location || 'India')}
                        </div>
                        
                        <!-- Notes Input -->
                        <div class="kanban-notes-wrapper">
                            <input type="text" class="kanban-notes-input"
                                   placeholder="Add note (interviewer, follow-up)..."
                                   value="${Utils.escapeHtml(item.notes || '')}"
                                   onchange="RoleBoard.updatePipelineNotes('${Utils.escapeHtml(item.id)}', this.value)" />
                        </div>

                        <!-- Card Actions & Move Dropdown -->
                        <div class="kanban-card-actions">
                            <select class="kanban-status-select" onchange="RoleBoard.updatePipelineStatus('${Utils.escapeHtml(item.id)}', this.value)">
                                <option value="saved" ${item.status === 'saved' ? 'selected' : ''}>Move: 📌 Saved</option>
                                <option value="applied" ${item.status === 'applied' ? 'selected' : ''}>Move: 📤 Applied</option>
                                <option value="interviewing" ${item.status === 'interviewing' ? 'selected' : ''}>Move: 🎤 Interviewing</option>
                                <option value="offered" ${item.status === 'offered' ? 'selected' : ''}>Move: 🎉 Offered</option>
                                <option value="rejected" ${item.status === 'rejected' ? 'selected' : ''}>Move: ⛔ Rejected</option>
                                <option value="__remove__">✕ Remove</option>
                            </select>
                            
                            <div class="kanban-btn-group">
                                ${item.url && item.url !== '#' ? `
                                    <a href="${Utils.escapeHtml(item.url)}" target="_blank" rel="noopener" class="kanban-icon-btn" title="Open Job Posting">
                                        <span class="material-symbols-outlined">open_in_new</span>
                                    </a>
                                ` : ''}
                                <button type="button" class="kanban-icon-btn delete" onclick="RoleBoard.removeFromPipeline('${Utils.escapeHtml(item.id)}')" title="Remove from Pipeline">
                                    <span class="material-symbols-outlined">delete</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        });

        this.updatePipelineBadges();
    },

    switchView(mode) {
        this.viewMode = mode;
        const tabBrowse = document.getElementById('tabBrowseFeed');
        const tabPipe = document.getElementById('tabPipeline');
        const feedHeader = document.getElementById('feedResultsHeader');
        const grid = document.getElementById('jobsGrid');
        const pagination = document.getElementById('pagination');
        const pipeContainer = document.getElementById('pipelineContainer');
        const pipeActions = document.getElementById('pipelineViewActions');

        if (mode === 'pipeline') {
            if (tabBrowse) tabBrowse.classList.remove('active');
            if (tabPipe) tabPipe.classList.add('active');
            if (feedHeader) feedHeader.style.display = 'none';
            if (grid) grid.style.display = 'none';
            if (pagination) pagination.style.display = 'none';
            if (pipeContainer) pipeContainer.style.display = 'block';
            if (pipeActions) pipeActions.style.display = 'flex';
            this.renderKanban();
        } else {
            if (tabPipe) tabPipe.classList.remove('active');
            if (tabBrowse) tabBrowse.classList.add('active');
            if (pipeContainer) pipeContainer.style.display = 'none';
            if (pipeActions) pipeActions.style.display = 'none';
            if (feedHeader) feedHeader.style.display = 'flex';
            if (grid) grid.style.display = 'grid';
            if (pagination) pagination.style.display = 'flex';
            this.renderJobs();
        }
    },

    // ========================================================================
    // Dynamic RSS Feeds & Outbound Webhook Alerts
    // ========================================================================

    openAlertsModal() {
        const overlay = document.getElementById('alertsModalOverlay');
        if (!overlay) return;
        overlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Construct current dynamic RSS URL
        const origin = window.location.origin;
        const params = new URLSearchParams();
        if (this.filters.domains && this.filters.domains.length) {
            params.set('domain', this.filters.domains.join(','));
        }
        if (this.filters.location) {
            params.set('location', this.filters.location);
        }
        if (this.filters.level) {
            params.set('level', this.filters.level);
        }

        const queryString = params.toString();
        const rssUrl = `${origin}/api/feed/rss${queryString ? '?' + queryString : ''}`;
        
        const urlInput = document.getElementById('rssFeedUrlInput');
        if (urlInput) urlInput.value = rssUrl;

        const filtersLabel = document.getElementById('rssActiveFiltersLabel');
        if (filtersLabel) {
            const parts = [];
            if (this.filters.domains && this.filters.domains.length) parts.push(this.filters.domains.join(', '));
            if (this.filters.location) parts.push(this.filters.location);
            if (this.filters.level) parts.push(this.filters.level);
            filtersLabel.textContent = parts.length > 0 ? parts.join(' • ') : 'All Active Roles';
        }

        // Restore saved webhook url
        const savedWebhook = localStorage.getItem('roleboard_webhook_url');
        const webhookInput = document.getElementById('webhookUrlInput');
        if (webhookInput && savedWebhook) webhookInput.value = savedWebhook;
    },

    closeAlertsModal() {
        const overlay = document.getElementById('alertsModalOverlay');
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = '';
    },

    copyRssUrl() {
        const input = document.getElementById('rssFeedUrlInput');
        const btn = document.getElementById('copyRssUrlBtn');
        if (!input) return;
        navigator.clipboard.writeText(input.value).then(() => {
            if (btn) {
                const orig = btn.innerHTML;
                btn.innerHTML = '<span class="material-symbols-outlined">check</span> COPIED!';
                setTimeout(() => { btn.innerHTML = orig; }, 2000);
            }
        });
    },

    async testWebhook() {
        const urlInput = document.getElementById('webhookUrlInput');
        const platformSelect = document.getElementById('webhookPlatformSelect');
        const statusText = document.getElementById('webhookStatusText');
        const btn = document.getElementById('testWebhookBtn');

        const webhookUrl = urlInput ? urlInput.value.trim() : '';
        const platform = platformSelect ? platformSelect.value : 'discord';

        if (!webhookUrl || !webhookUrl.startsWith('http')) {
            if (statusText) {
                statusText.style.color = '#d93829';
                statusText.textContent = 'Please enter a valid HTTP/HTTPS Webhook URL';
            }
            return;
        }

        // Save URL for future visits
        localStorage.setItem('roleboard_webhook_url', webhookUrl);

        if (statusText) {
            statusText.style.color = '#383838';
            statusText.textContent = 'Dispatching test notification...';
        }
        if (btn) btn.disabled = true;

        try {
            const sampleJob = (this.jobs && this.jobs.length > 0) ? this.jobs[0] : {
                role: 'Senior Software Engineer',
                company: 'MotherDuck Partner',
                location: 'Remote, India',
                domain: 'Engineering',
                level: 'Senior Level',
                url: 'https://www.linkedin.com/jobs/'
            };

            const response = await fetch('/api/webhook/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    webhook_url: webhookUrl,
                    platform: platform,
                    job: sampleJob
                })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                if (statusText) {
                    statusText.style.color = '#2e7d32';
                    statusText.textContent = `✓ ${result.message || 'Webhook delivered successfully!'}`;
                }
            } else {
                throw new Error(result.error || `Server responded with ${response.status}`);
            }
        } catch (err) {
            if (statusText) {
                statusText.style.color = '#d93829';
                statusText.textContent = `❌ ${err.message}`;
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    }
};

// Expose globally
window.RoleBoard = RoleBoard;
