/**
 * Sparkles Particle Animation
 * Inspired by Aceternity UI Sparkles component
 * Features: Flowing particles, smooth motion, fade effects, mouse interaction
 * Vanilla JS implementation for Flask + vanilla JS stack
 */

class Sparkles {
    constructor(containerId = 'sparkles-background', options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Sparkles: Container element not found');
            return;
        }

        console.log('Sparkles: Initializing...');

        // Configuration (extracted from React component defaults)
        this.config = {
            minSize: options.minSize || 0.6,
            maxSize: options.maxSize || 1.4,
            speed: options.speed || 1,
            particleColor: options.particleColor || '#FFFFFF',
            particleDensity: options.particleDensity || 100,
            background: options.background || 'transparent'
        };

        // State
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.mouse = { x: -1000, y: -1000 };
        this.animationId = null;
        this.opacity = 0;
        this.targetOpacity = 1;
        this.isLoaded = false;

        this.init();
    }

    init() {
        console.log('Sparkles: init() called');
        this.setupCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.setupResizeObserver();
        
        // Mark as loaded immediately (like React component's particlesLoaded callback)
        this.isLoaded = true;
        console.log('Sparkles: Particles loaded and ready');
        
        this.animate();
        console.log('Sparkles: Initialization complete. Particles created:', this.particles.length);
    }

    setupCanvas() {
        console.log('Sparkles: Setting up canvas');

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

        console.log('Sparkles: Canvas setup complete');
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;

        if (this.ctx) {
            this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        console.log('Sparkles: Canvas resized to', rect.width, 'x', rect.height, 'DPR:', dpr);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 255, g: 255, b: 255 };
    }

    createParticles() {
        const rect = this.container.getBoundingClientRect();
        const area = rect.width * rect.height;
        // Calculate particle count based on density (similar to React component)
        const baseCount = Math.floor((area / 40000) * this.config.particleDensity);
        const count = Math.max(50, Math.min(baseCount, 500)); // Clamp between 50-500

        this.particles = [];
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * rect.width,
                y: Math.random() * rect.height,
                size: this.config.minSize + Math.random() * (this.config.maxSize - this.config.minSize),
                speedX: (Math.random() - 0.5) * this.config.speed * 0.5,
                speedY: (Math.random() - 0.5) * this.config.speed * 0.5,
                opacity: 0.1 + Math.random() * 0.9,
                opacitySpeed: 0.02 + Math.random() * 0.02,
                opacityDirection: Math.random() > 0.5 ? 1 : -1
            });
        }
    }

    setupEventListeners() {
        console.log('Sparkles: Setting up event listeners');

        const handleMouseMove = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        };

        const handleMouseLeave = () => {
            this.mouse = { x: -1000, y: -1000 };
        };

        this.container.addEventListener('mousemove', handleMouseMove);
        this.container.addEventListener('mouseleave', handleMouseLeave);

        console.log('Sparkles: Event listeners attached');
    }

    setupResizeObserver() {
        const resizeObserver = new ResizeObserver(() => {
            this.createParticles();
        });
        resizeObserver.observe(this.container);
    }

    updateParticles() {
        const rect = this.container.getBoundingClientRect();

        for (const particle of this.particles) {
            // Update position (flowing motion like React component)
            particle.x += particle.speedX;
            particle.y += particle.speedY;

            // Wrap around edges (continuous flow)
            if (particle.x < 0) particle.x = rect.width;
            if (particle.x > rect.width) particle.x = 0;
            if (particle.y < 0) particle.y = rect.height;
            if (particle.y > rect.height) particle.y = 0;

            // Animate opacity (twinkle effect)
            particle.opacity += particle.opacitySpeed * particle.opacityDirection;
            
            if (particle.opacity >= 1) {
                particle.opacity = 1;
                particle.opacityDirection = -1;
            } else if (particle.opacity <= 0.1) {
                particle.opacity = 0.1;
                particle.opacityDirection = 1;
            }

            // Mouse interaction - push particles away (from React component onClick mode: "push")
            const dx = particle.x - this.mouse.x;
            const dy = particle.y - this.mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 100 && distance > 0) {
                const force = (100 - distance) / 100;
                particle.x += (dx / distance) * force * 2;
                particle.y += (dy / distance) * force * 2;
            }
        }
    }

    draw() {
        if (!this.ctx) {
            console.error('Sparkles: No context available');
            return;
        }

        if (!this.isLoaded) {
            return;
        }

        const dpr = window.devicePixelRatio || 1;
        const width = this.canvas.width / dpr;
        const height = this.canvas.height / dpr;
        
        this.ctx.clearRect(0, 0, width, height);

        // Fade in effect (like React component's motion.div with controls)
        if (this.opacity < this.targetOpacity) {
            this.opacity = Math.min(this.opacity + 0.02, this.targetOpacity);
        }

        this.updateParticles();

        const particleRgb = this.hexToRgb(this.config.particleColor);

        // Debug: log first frame
        if (this.opacity === 0.02) {
            console.log('Sparkles: First render - particles:', this.particles.length, 'opacity:', this.opacity);
        }

        // Draw each particle
        for (const particle of this.particles) {
            const radius = particle.size / 2;
            const alpha = particle.opacity * this.opacity;

            // Draw glow (radial gradient for soft edges)
            const gradient = this.ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, radius * 3
            );
            gradient.addColorStop(0, `rgba(${particleRgb.r}, ${particleRgb.g}, ${particleRgb.b}, ${alpha * 0.6})`);
            gradient.addColorStop(0.5, `rgba(${particleRgb.r}, ${particleRgb.g}, ${particleRgb.b}, ${alpha * 0.2})`);
            gradient.addColorStop(1, `rgba(${particleRgb.r}, ${particleRgb.g}, ${particleRgb.b}, 0)`);

            // Draw glow
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, radius * 3, 0, Math.PI * 2);
            this.ctx.fillStyle = gradient;
            this.ctx.fill();

            // Draw core particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${particleRgb.r}, ${particleRgb.g}, ${particleRgb.b}, ${alpha})`;
            this.ctx.fill();
        }

        this.animationId = requestAnimationFrame(() => this.draw());
    }

    animate() {
        this.draw();
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas) {
            this.canvas.remove();
        }
    }
}

window.Sparkles = Sparkles;
