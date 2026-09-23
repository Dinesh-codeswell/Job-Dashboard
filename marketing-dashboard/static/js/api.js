/**
 * API Module for RoleBoard Dashboard
 * Includes client-side caching for instant UI responses
 */
const API = {
    baseURL: '',
    _cache: new Map(),
    _cacheTTL: 15000, // 15 seconds client cache for instant pagination / filter switches

    clearCache() {
        this._cache.clear();
    },

    async request(endpoint, options = {}, maxRetries = 2) {
        const url = `${this.baseURL}${endpoint}`;
        const isGet = !options.method || options.method === 'GET';

        // Check client-side memory cache for GET requests
        if (isGet) {
            const cached = this._cache.get(url);
            if (cached && (Date.now() - cached.timestamp < this._cacheTTL)) {
                return cached.data;
            }
        }

        const config = {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        };

        let lastError = null;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                const response = await fetch(url, config);
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'API request failed');

                if (isGet) {
                    this._cache.set(url, { data, timestamp: Date.now() });
                }

                return data;
            } catch (error) {
                lastError = error;
                if (attempt < maxRetries) {
                    const delay = 300 * Math.pow(2, attempt);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        throw lastError;
    },

    async get(endpoint, params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== undefined && v !== null && v !== '') {
                cleanParams[k] = v;
            }
        }
        const qs = new URLSearchParams(cleanParams).toString();
        const url = qs ? `${endpoint}?${qs}` : endpoint;
        return this.request(url, { method: 'GET' });
    },

    async post(endpoint, data = {}) {
        this.clearCache(); // Mutating request clears cached data
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) });
    },

    // ========================================================================
    // API Methods
    // ========================================================================

    async getJobs(page = 1, limit = 30, filters = {}, includeMeta = false) {
        const params = { page, limit, ...filters };
        if (includeMeta) {
            params.include_meta = 'true';
        }
        return this.get('/api/jobs', params);
    },

    async getStats() {
        return this.get('/api/stats');
    },

    async getDomains() {
        return this.get('/api/domains');
    },

    async getLocations() {
        return this.get('/api/locations');
    },

    async refreshData() {
        this.clearCache();
        return this.post('/api/refresh');
    },

    async healthCheck() {
        return this.get('/api/health');
    }
};

