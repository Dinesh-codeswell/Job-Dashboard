/**
 * API Module for RoleBoard Dashboard
 */
const API = {
    baseURL: '',

    async request(endpoint, options = {}, maxRetries = 2) {
        const url = `${this.baseURL}${endpoint}`;
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
                return data;
            } catch (error) {
                lastError = error;
                if (attempt < maxRetries) {
                    const delay = 500 * Math.pow(2, attempt);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        throw lastError;
    },

    async get(endpoint, params = {}) {
        const qs = new URLSearchParams(params).toString();
        const url = qs ? `${endpoint}?${qs}` : endpoint;
        return this.request(url, { method: 'GET' });
    },

    async post(endpoint, data = {}) {
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) });
    },

    // ========================================================================
    // API Methods
    // ========================================================================

    async getJobs(page = 1, limit = 30, filters = {}) {
        const params = { page, limit, ...filters };
        return this.get('/api/jobs', params);
    },

    async getStats() {
        return this.get('/api/stats');
    },

    async getDomains() {
        return this.get('/api/domains');
    },

    async refreshData() {
        return this.post('/api/refresh');
    },

    async healthCheck() {
        return this.get('/api/health');
    }
};
