/**
 * Footer Dot Pattern Animation
 * Creates an interactive dot background effect for the footer
 */

class FooterDotPattern {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.options = {
            dotSize: options.dotSize || 2,
            gap: options.gap || 20,
            baseColor: options.baseColor || '#3e4942',
            glowColor: options.glowColor || '#73daa9',
            proximity: options.proximity || 100,
            glowIntensity: options.glowIntensity || 0.6,
            ...options
        };

        this.canvas = null;
        this.ctx = null;
        this.dots = [];
        this.mouse = { x: -9999, y: -9999 };
        this.animationFrame = null;

        this.init();
    }

    init() {
        this.createCanvas();
        this.createDots();
        this.bindEvents();
        this.animate();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.canvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        `;

        this.container.style.position = 'relative';
        this.container.insertBefore(this.canvas, this.container.firstChild);

        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.createDots();
    }

    createDots() {
        this.dots = [];
        const cols = Math.ceil(this.canvas.width / this.options.gap);
        const rows = Math.ceil(this.canvas.height / this.options.gap);

        for (let i = 0; i < cols; i++) {
            for (let j = 0; j < rows; j++) {
                this.dots.push({
                    x: i * this.options.gap + this.options.gap / 2,
                    y: j * this.options.gap + this.options.gap / 2,
                    baseRadius: this.options.dotSize,
                    currentRadius: this.options.dotSize,
                    opacity: 0.4
                });
            }
        }
    }

    bindEvents() {
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
        });

        this.container.addEventListener('mouseleave', () => {
            this.mouse.x = -9999;
            this.mouse.y = -9999;
        });
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.dots.forEach(dot => {
            const dx = this.mouse.x - dot.x;
            const dy = this.mouse.y - dot.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // Calculate glow effect based on mouse proximity
            let glowFactor = 0;
            if (distance < this.options.proximity) {
                glowFactor = Math.pow(1 - distance / this.options.proximity, 2);
            }

            // Smooth radius transition
            const targetRadius = dot.baseRadius + glowFactor * 2;
            dot.currentRadius += (targetRadius - dot.currentRadius) * 0.1;
            dot.opacity = 0.4 + glowFactor * this.options.glowIntensity;

            // Draw dot
            this.ctx.beginPath();
            this.ctx.arc(dot.x, dot.y, dot.currentRadius, 0, Math.PI * 2);
            
            // Create gradient for glow
            if (glowFactor > 0.01) {
                const gradient = this.ctx.createRadialGradient(
                    dot.x, dot.y, 0,
                    dot.x, dot.y, dot.currentRadius * 3
                );
                gradient.addColorStop(0, this.options.glowColor + Math.floor(glowFactor * 255).toString(16).padStart(2, '0'));
                gradient.addColorStop(1, 'transparent');
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            }

            // Draw solid dot
            this.ctx.beginPath();
            this.ctx.arc(dot.x, dot.y, dot.currentRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = this.hexToRgba(this.options.baseColor, dot.opacity);
            this.ctx.fill();
        });

        this.animationFrame = requestAnimationFrame(() => this.animate());
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const footerElement = document.querySelector('.footer-dot-background');
    if (footerElement && !footerElement.id) {
        footerElement.id = 'footer-dot-bg';
    }
    
    if (footerElement) {
        try {
            new FooterDotPattern('footer-dot-bg', {
                dotSize: 1.5,
                gap: 20,
                baseColor: '#3e4942',
                glowColor: '#73daa9',
                proximity: 100,
                glowIntensity: 0.6
            });
        } catch (error) {
            console.error('Footer dot pattern initialization failed:', error);
        }
    }
});

// Export for manual initialization if needed
if (typeof window !== 'undefined') {
    window.FooterDotPattern = FooterDotPattern;
}
