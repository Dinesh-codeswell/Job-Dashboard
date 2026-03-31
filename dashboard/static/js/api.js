/**
 * API Module for Consulting Jobs Dashboard
 * Handles all API calls to the backend
 */

const API = {
    baseURL: '',
    
    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    },
    
    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // ========================================================================
    // API Methods
    // ========================================================================
    
    /**
     * Get paginated jobs list
     */
    async getJobs(page = 1, limit = 30, filters = {}) {
        const params = { page, limit, ...filters };
        return this.get('/api/jobs', params);
    },
    
    /**
     * Get single job details
     */
    async getJob(jobId) {
        return this.get(`/api/jobs/${jobId}`);
    },
    
    /**
     * Get dashboard statistics
     */
    async getStats() {
        return this.get('/api/stats');
    },
    
    /**
     * Get list of cities
     */
    async getCities() {
        return this.get('/api/cities');
    },
    
    /**
     * Get list of employment types
     */
    async getEmploymentTypes() {
        return this.get('/api/employment-types');
    },
    
    /**
     * Refresh data from Google Sheets
     */
    async refreshData() {
        return this.post('/api/refresh');
    },
    
    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/api/health');
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
