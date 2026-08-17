/**
 * Utility Functions for RoleBoard Dashboard
 */
const Utils = {
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Format relative time
     */
    formatDate(dateString) {
        if (!dateString) return 'Recently';
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;

            return date.toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch {
            return dateString || 'Recently';
        }
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Get domain class for styling (job card badge)
     */
    getDomainClass(domain) {
        const map = {
            'Software Engineer': 'software-engineer',
            'Data Analyst': 'data-analyst',
            'Data Engineer': 'data-engineer',
            'Data Science': 'data-science',
            'ML Engineer': 'ml-engineer',
            'DevOps & Cloud': 'devops',
            'QA & Testing': 'qa',
            'Security': 'security',
            'Support': 'support',
            'Operations': 'operations',
            'Marketing': 'marketing',
            'UI/UX': 'uiux',
            'Product': 'product',
            'Founders Office': 'founders'
        };
        return map[domain] || 'other';
    },

    /**
     * Tag colors (used for filter dropdown dots and card accents)
     */
    DOMAIN_COLORS: {
        'Software Engineer': '#cfe8ff',
        'Data Analyst': '#d8f3dc',
        'Data Engineer': '#e5dbff',
        'Data Science': '#ffe4e6',
        'ML Engineer': '#ede9fe',
        'DevOps & Cloud': '#ffedd5',
        'QA & Testing': '#ecfccb',
        'Security': '#fee2e2',
        'Support': '#ccfbf1',
        'Operations': '#fef3c7',
        'Marketing': '#ffe95c',
        'UI/UX': '#d5f5c2',
        'Product': '#ffb347',
        'Founders Office': '#f6d0ff'
    },

    getLevelClass(level) {
        const map = {
            'Entry Level': 'level-entry',
            'Mid Level': 'level-mid',
            'Senior Level': 'level-senior'
        };
        return map[level] || '';
    }
};
