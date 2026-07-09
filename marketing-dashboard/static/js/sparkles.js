/**
 * Sparkles Particle Animation for RoleBoard Dashboard
 * Vanilla JS implementation inspired by Aceternity UI Sparkles
 */
class Sparkles {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.config = {
            minSize: options.minSize || 0.6,
            maxSize: options.maxSize || 1.4,
            speed: options.speed || 1,
            particleColor: options.particleColor || '#1a3300',
            particleDensity: options.particleDensity || 60,
            background: options.background || 'transparent'
        };

        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.mouse = { x: -1000, y: -1000 };
        this.animationId = null;
        this.opacity = 0;
        this.targetOpacity = 1;

        this.init();
    }

    init() {
        this.setupCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.setupResizeObserver();
        this.animate();
    }

    setupCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.cssText = `
            display: block;
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        `;
        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
        if (this.ctx) this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 26, g: 51, b: 0 };
    }

    createParticles() {
        const rect = this.container.getBoundingClientRect();
        const area = rect.width * rect.height;
        const baseCount = Math.floor((area / 40000) * this.config.particleDensity);
        const count = Math.max(30, Math.min(baseCount, 300));

        this.particles = [];
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * rect.width,
                y: Math.random() * rect.height,
                size: this.config.minSize + Math.random() * (this.config.maxSize - this.config.minSize),
                speedX: (Math.random() - 0.5) * this.config.speed * 0.3,
                speedY: (Math.random() - 0.5) * this.config.speed * 0.3,
                opacity: 0.1 + Math.random() * 0.6,
                opacitySpeed: 0.01 + Math.random() * 0.02,
                opacityDirection: Math.random() > 0.5 ? 1 : -1
            });
        }
    }

    setupEventListeners() {
        const handleMouseMove = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        };
        const handleMouseLeave = () => { this.mouse = { x: -1000, y: -1000 }; };
        this.container.addEventListener('mousemove', handleMouseMove);
        this.container.addEventListener('mouseleave', handleMouseLeave);
    }

    setupResizeObserver() {
        const resizeObserver = new ResizeObserver(() => this.createParticles());
        resizeObserver.observe(this.container);
    }

    updateParticles() {
        const rect = this.container.getBoundingClientRect();

        for (const particle of this.particles) {
            particle.x += particle.speedX;
            particle.y += particle.speedY;

            if (particle.x < 0) particle.x = rect.width;
            if (particle.x > rect.width) particle.x = 0;
            if (particle.y < 0) particle.y = rect.height;
            if (particle.y > rect.height) particle.y = 0;

            particle.opacity += particle.opacitySpeed * particle.opacityDirection;
            if (particle.opacity >= 0.7) {
                particle.opacity = 0.7;
                particle.opacityDirection = -1;
            } else if (particle.opacity <= 0.05) {
                particle.opacity = 0.05;
                particle.opacityDirection = 1;
            }

            const dx = particle.x - this.mouse.x;
            const dy = particle.y - this.mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 100 && distance > 0) {
                const force = (100 - distance) / 100;
                particle.x += (dx / distance) * force * 1.5;
                particle.y += (dy / distance) * force * 1.5;
            }
        }
    }

    draw() {
        if (!this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const width = this.canvas.width / dpr;
        const height = this.canvas.height / dpr;

        this.ctx.clearRect(0, 0, width, height);

        if (this.opacity < this.targetOpacity) {
            this.opacity = Math.min(this.opacity + 0.02, this.targetOpacity);
        }

        this.updateParticles();

        const rgb = this.hexToRgb(this.config.particleColor);

        for (const particle of this.particles) {
            const radius = particle.size / 2;
            const alpha = particle.opacity * this.opacity * 0.4;

            const gradient = this.ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, radius * 4
            );
            gradient.addColorStop(0, `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha * 0.5})`);
            gradient.addColorStop(1, `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0)`);

            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, radius * 4, 0, Math.PI * 2);
            this.ctx.fillStyle = gradient;
            this.ctx.fill();

            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
            this.ctx.fill();
        }

        this.animationId = requestAnimationFrame(() => this.draw());
    }

    animate() {
        this.draw();
    }

    destroy() {
        if (this.animationId) cancelAnimationFrame(this.animationId);
        if (this.canvas) this.canvas.remove();
    }
}

window.Sparkles = Sparkles;
