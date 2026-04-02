/**
 * Dot Pattern Background Animation
 * Inspired by shadcn/ui DotPattern component
 * Features: Wave animation, mouse proximity glow, smooth interactions
 */

class DotPattern {
    constructor(containerId = 'dot-background', options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('DotPattern: Container element not found');
            return;
        }

        console.log('DotPattern: Initializing...');

        // Configuration
        this.config = {
            dotSize: options.dotSize || 2,
            gap: options.gap || 24,
            baseColor: options.baseColor || '#404040',
            glowColor: options.glowColor || '#22d3ee',
            proximity: options.proximity || 120,
            glowIntensity: options.glowIntensity || 1,
            waveSpeed: options.waveSpeed || 0.5
        };

        // State
        this.canvas = null;
        this.ctx = null;
        this.dots = [];
        this.mouse = { x: -1000, y: -1000 };
        this.animationId = null;
        this.startTime = Date.now();

        this.init();
    }

    init() {
        console.log('DotPattern: init() called');
        this.setupCanvas();
        this.buildGrid();
        this.setupEventListeners();
        this.setupResizeObserver();
        this.animate();
        console.log('DotPattern: Initialization complete. Dots created:', this.dots.length);
        
        // Force resize after a short delay to ensure container has proper dimensions
        setTimeout(() => {
            this.buildGrid();
            console.log('DotPattern: Forced resize. New dot count:', this.dots.length);
        }, 100);
    }

    setupCanvas() {
        console.log('DotPattern: Setting up canvas');
        
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
        
        console.log('DotPattern: Canvas setup complete. Container size:', 
            this.container.clientWidth, 'x', this.container.clientHeight);
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;

        if (this.ctx) {
            this.ctx.scale(dpr, dpr);
        }
        
        console.log('DotPattern: Canvas resized. Client rect:', rect.width, 'x', rect.height, 'DPR:', dpr);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    buildGrid() {
        this.resizeCanvas();

        const rect = this.container.getBoundingClientRect();
        const cellSize = this.config.dotSize + this.config.gap;
        const cols = Math.ceil(rect.width / cellSize) + 1;
        const rows = Math.ceil(rect.height / cellSize) + 1;

        const offsetX = (rect.width - (cols - 1) * cellSize) / 2;
        const offsetY = (rect.height - (rows - 1) * cellSize) / 2;

        this.dots = [];
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                this.dots.push({
                    x: offsetX + col * cellSize,
                    y: offsetY + row * cellSize,
                    baseOpacity: 0.3 + Math.random() * 0.2
                });
            }
        }
    }

    setupEventListeners() {
        console.log('DotPattern: Setting up event listeners');

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

        // Add listeners to both container and canvas
        this.container.addEventListener('mousemove', handleMouseMove);
        this.container.addEventListener('mouseleave', handleMouseLeave);
        
        if (this.canvas) {
            this.canvas.addEventListener('mousemove', handleMouseMove);
            this.canvas.addEventListener('mouseleave', handleMouseLeave);
        }

        console.log('DotPattern: Event listeners attached');
    }

    setupResizeObserver() {
        const resizeObserver = new ResizeObserver(() => {
            this.buildGrid();
        });
        resizeObserver.observe(this.container);
    }

    smoothstep(edge0, edge1, x) {
        const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
        return t * t * (3 - 2 * t);
    }

    draw() {
        if (!this.ctx) return;

        const dpr = window.devicePixelRatio || 1;
        this.ctx.clearRect(0, 0, this.canvas.width / dpr, this.canvas.height / dpr);

        const { x: mx, y: my } = this.mouse;
        const proxSq = this.config.proximity * this.config.proximity;
        const time = (Date.now() - this.startTime) * 0.001 * this.config.waveSpeed;

        const baseRgb = this.hexToRgb(this.config.baseColor);
        const glowRgb = this.hexToRgb(this.config.glowColor);

        // Debug: log mouse position occasionally
        if (this.mouse.x > -500 && Math.random() < 0.01) {
            console.log('DotPattern: Mouse at', this.mouse.x, this.mouse.y);
        }

        for (const dot of this.dots) {
            const dx = dot.x - mx;
            const dy = dot.y - my;
            const distSq = dx * dx + dy * dy;

            // Wave animation
            const wave = Math.sin(dot.x * 0.02 + dot.y * 0.02 + time) * 0.5 + 0.5;
            const waveOpacity = dot.baseOpacity + wave * 0.15;
            const waveScale = 1 + wave * 0.2;

            let opacity = waveOpacity;
            let scale = waveScale;
            let r = baseRgb.r;
            let g = baseRgb.g;
            let b = baseRgb.b;
            let glow = 0;

            // Mouse proximity effect
            if (distSq < proxSq) {
                const dist = Math.sqrt(distSq);
                const t = 1 - dist / this.config.proximity;
                const easedT = this.smoothstep(0, 1, t);

                // Interpolate color
                r = Math.round(baseRgb.r + (glowRgb.r - baseRgb.r) * easedT);
                g = Math.round(baseRgb.g + (glowRgb.g - baseRgb.g) * easedT);
                b = Math.round(baseRgb.b + (glowRgb.b - baseRgb.b) * easedT);

                opacity = Math.min(1, waveOpacity + easedT * 0.7);
                scale = waveScale + easedT * 0.8;
                glow = easedT * this.config.glowIntensity;
            }

            const radius = (this.config.dotSize / 2) * scale;

            // Draw glow
            if (glow > 0) {
                const gradient = this.ctx.createRadialGradient(
                    dot.x, dot.y, 0,
                    dot.x, dot.y, radius * 4
                );
                gradient.addColorStop(0, `rgba(${glowRgb.r}, ${glowRgb.g}, ${glowRgb.b}, ${glow * 0.4})`);
                gradient.addColorStop(0.5, `rgba(${glowRgb.r}, ${glowRgb.g}, ${glowRgb.b}, ${glow * 0.1})`);
                gradient.addColorStop(1, `rgba(${glowRgb.r}, ${glowRgb.g}, ${glowRgb.b}, 0)`);
                
                this.ctx.beginPath();
                this.ctx.arc(dot.x, dot.y, radius * 4, 0, Math.PI * 2);
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            }

            // Draw dot
            this.ctx.beginPath();
            this.ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${opacity})`;
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

window.DotPattern = DotPattern;
