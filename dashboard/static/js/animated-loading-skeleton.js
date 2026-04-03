/**
 * Animated Loading Skeleton with Search Icon Animation
 * Inspired by Aceternity UI Animated Loading Skeleton
 * Optimized for dark theme (Beyond Career design system)
 * Features: Floating search icon, shimmer cards, staggered animations
 * 
 * IMPORTANT: This skeleton is designed to work WITH the existing job grid structure.
 * It creates individual skeleton cards that match the real job card dimensions.
 */

class AnimatedLoadingSkeleton {
    constructor(containerId = 'loading-skeleton', options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('AnimatedLoadingSkeleton: Container not found');
            return;
        }

        console.log('AnimatedLoadingSkeleton: Initializing...');

        // Configuration - MATCHES REAL JOB CARDS
        this.config = {
            numCards: options.numCards || 6,
            shimmerSpeed: options.shimmerSpeed || 1.5,
            searchIconColor: options.searchIconColor || '#73daa9',
            cardMinHeight: options.cardMinHeight || 280,
            ...options
        };

        // State
        this.animationFrame = null;
        this.searchIconPos = { x: 0, y: 0 };
        this.startTime = Date.now();
        this.cardPositions = [];
        this.shuffledPositions = [];
        this.isDestroyed = false;

        this.init();
    }

    init() {
        console.log('AnimatedLoadingSkeleton: init() called');
        this.buildSkeleton();
        
        // Delay search icon animation to ensure cards are rendered
        setTimeout(() => {
            this.calculateCardPositions();
            this.startSearchIconAnimation();
        }, 100);
        
        this.startShimmerAnimation();
        console.log('AnimatedLoadingSkeleton: Initialization complete');
    }

    buildSkeleton() {
        console.log('AnimatedLoadingSkeleton: Building skeleton');
        
        const cardsHTML = this.generateCards();

        // Don't create a wrapper with its own grid - just place cards directly
        // The parent container (jobsGrid) already has the grid classes
        this.container.innerHTML = `
            <!-- Floating Search Icon -->
            <div id="search-icon-container" class="search-icon-container">
                <div class="search-icon-glow">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>

            <!-- Skeleton Cards - Placed directly in parent grid -->
            ${cardsHTML}
        `;
        
        console.log('AnimatedLoadingSkeleton: Skeleton built');
    }

    generateCards() {
        let cardsHTML = '';
        
        for (let i = 0; i < this.config.numCards; i++) {
            const delay = i * 0.1;
            cardsHTML += `
                <div class="skeleton-card-animated" style="animation-delay: ${delay}s">
                    <!-- Card Header/Logo Placeholder -->
                    <div class="skeleton-card-header">
                        <div class="skeleton-shimmer"></div>
                    </div>
                    
                    <!-- Card Title Placeholder -->
                    <div class="skeleton-card-title">
                        <div class="skeleton-shimmer" style="width: 75%"></div>
                    </div>
                    
                    <!-- Card Company/Subtitle Placeholder -->
                    <div class="skeleton-card-subtitle">
                        <div class="skeleton-shimmer" style="width: 50%"></div>
                    </div>
                    
                    <!-- Card Meta Placeholders (Location, Type, etc.) -->
                    <div class="skeleton-card-meta">
                        <div class="skeleton-shimmer" style="width: 60%"></div>
                        <div class="skeleton-shimmer" style="width: 40%"></div>
                    </div>
                </div>
            `;
        }

        return cardsHTML;
    }

    calculateCardPositions() {
        const cards = this.container.querySelectorAll('.skeleton-card-animated');
        
        if (cards.length === 0) return;
        
        this.cardPositions = [];
        const containerRect = this.container.getBoundingClientRect();

        cards.forEach((card, index) => {
            const rect = card.getBoundingClientRect();
            
            this.cardPositions.push({
                x: rect.left - containerRect.left + rect.width / 2,
                y: rect.top - containerRect.top + rect.height / 2
            });
        });

        // Shuffle positions for random animation path (use 4 random cards)
        this.shuffledPositions = [...this.cardPositions]
            .sort(() => Math.random() - 0.5)
            .slice(0, Math.min(4, this.cardPositions.length));
        
        // Ensure loop completion by adding first position at end
        if (this.shuffledPositions.length > 0) {
            this.shuffledPositions.push(this.shuffledPositions[0]);
        }
        
        // Position the search icon container at the top of the grid with offset
        const iconContainer = this.container.querySelector('#search-icon-container');
        if (iconContainer) {
            // Add some top padding so icon doesn't overlap with edge
            iconContainer.style.marginTop = '20px';
        }
        
        console.log('AnimatedLoadingSkeleton: Card positions calculated', this.shuffledPositions.length);
    }

    startSearchIconAnimation() {
        const iconContainer = this.container.querySelector('#search-icon-container');
        if (!iconContainer || this.shuffledPositions.length === 0) return;

        let currentIndex = 0;
        const animationSpeed = 2000;

        const animate = () => {
            if (this.isDestroyed) return;

            const target = this.shuffledPositions[currentIndex];
            const nextIndex = (currentIndex + 1) % this.shuffledPositions.length;

            // Use transform for positioning to keep icon within container bounds
            // This ensures icon stays within skeleton section only
            iconContainer.style.transition = `all ${animationSpeed}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            iconContainer.style.left = `${target.x}px`;
            iconContainer.style.top = `${target.y}px`;
            iconContainer.style.transform = 'translate(-50%, -50%) scale(1.2)';
            iconContainer.style.position = 'absolute';
            iconContainer.style.marginTop = '0';

            setTimeout(() => {
                iconContainer.style.transform = 'translate(-50%, -50%) scale(1)';
            }, animationSpeed / 2);

            currentIndex = nextIndex;
            this.animationFrame = setTimeout(animate, animationSpeed);
        };

        // Set initial position to first card
        if (this.shuffledPositions.length > 0) {
            const first = this.shuffledPositions[0];
            iconContainer.style.left = `${first.x}px`;
            iconContainer.style.top = `${first.y}px`;
            iconContainer.style.position = 'absolute';
        }

        animate();
        console.log('AnimatedLoadingSkeleton: Search icon animation started');
    }

    startShimmerAnimation() {
        const shimmers = this.container.querySelectorAll('.skeleton-shimmer');
        
        shimmers.forEach((shimmer, index) => {
            shimmer.style.animation = `skeletonShimmer ${this.config.shimmerSpeed}s ease-in-out infinite`;
            shimmer.style.animationDelay = `${index * 0.1}s`;
        });

        console.log('AnimatedLoadingSkeleton: Shimmer animation started');
    }

    destroy() {
        console.log('AnimatedLoadingSkeleton: Destroying');
        this.isDestroyed = true;
        
        if (this.animationFrame) {
            clearTimeout(this.animationFrame);
        }
        
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    static async showWithMinimumTime(containerId = 'loading-skeleton', options = {}, minimumTime = 1000) {
        const startTime = Date.now();
        
        return new Promise((resolve) => {
            const skeleton = new AnimatedLoadingSkeleton(containerId, options);
            
            const elapsedTime = Date.now() - startTime;
            const remainingTime = Math.max(0, minimumTime - elapsedTime);
            
            setTimeout(() => {
                resolve(skeleton);
            }, remainingTime);
        });
    }
}

// Add CSS styles dynamically
function injectSkeletonStyles() {
    if (document.getElementById('animated-skeleton-styles')) return;

    const style = document.createElement('style');
    style.id = 'animated-skeleton-styles';
    style.textContent = `
        /* ============================================================================
           ANIMATED LOADING SKELETON - Dark Theme Optimized
           Matches dimensions of real job cards exactly
           
           IMPORTANT: We apply grid EXPLICITLY here to guarantee it works,
           rather than relying on parent grid classes.
           ============================================================================ */

        /* Force grid on the container (jobsGrid) */
        #jobsGrid {
            display: grid !important;
            grid-template-columns: repeat(1, minmax(0, 1fr));
            gap: 2rem;
        }

        @media (min-width: 768px) {
            #jobsGrid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }

        @media (min-width: 1024px) {
            #jobsGrid {
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            }
        }

        /* Skeleton Card - MATCHES real job card dimensions */
        .skeleton-card-animated {
            position: relative;
            background: #1f1f1f;
            border-radius: 1.5rem;
            padding: 1.5rem;
            min-height: 280px;
            border: 1px solid rgba(62, 73, 66, 0.2);
            border-top: 1px solid rgba(62, 73, 66, 0.2);
            opacity: 0;
            transform: translateY(20px);
            animation: cardFadeIn 0.4s ease-out forwards;
            overflow: hidden;
        }

        @keyframes cardFadeIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Card Sections - Structured to match real card layout */
        .skeleton-card-header {
            width: 3.5rem;
            height: 3.5rem;
            background: #2a2a2a;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            overflow: hidden;
            border: 2px solid rgba(62, 73, 66, 0.3);
        }

        .skeleton-card-title {
            height: 0.75rem;
            margin-bottom: 0.75rem;
            overflow: hidden;
        }

        .skeleton-card-subtitle {
            height: 0.75rem;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }

        .skeleton-card-meta {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .skeleton-card-meta .skeleton-shimmer {
            height: 0.625rem;
            border-radius: 0.375rem;
        }

        /* Shimmer Effect */
        .skeleton-shimmer {
            height: 100%;
            background: linear-gradient(
                90deg,
                #2a2a2a 0%,
                #353535 50%,
                #2a2a2a 100%
            );
            background-size: 200% 100%;
            border-radius: 0.375rem;
        }

        @keyframes skeletonShimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }

        /* Search Icon Container */
        .search-icon-container {
            position: absolute;
            z-index: 10;
            pointer-events: none;
            left: 0;
            top: 0;
            transition: all 2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Ensure parent container has relative positioning */
        #jobsGrid {
            position: relative !important;
            overflow: hidden; /* Prevent icon from going outside */
        }

        .search-icon-glow {
            background: rgba(115, 218, 169, 0.15);
            padding: 0.75rem;
            border-radius: 9999px;
            backdrop-filter: blur(8px);
            box-shadow: 
                0 0 20px rgba(115, 218, 169, 0.2),
                0 0 35px rgba(115, 218, 169, 0.4),
                0 0 20px rgba(115, 218, 169, 0.2);
            animation: searchIconPulse 1s ease-in-out infinite;
        }

        .search-icon {
            width: 1.5rem;
            height: 1.5rem;
            color: #73daa9;
        }

        @keyframes searchIconPulse {
            0%, 100% {
                box-shadow: 
                    0 0 20px rgba(115, 218, 169, 0.2),
                    0 0 35px rgba(115, 218, 169, 0.4);
                transform: scale(1);
            }
            50% {
                box-shadow: 
                    0 0 30px rgba(115, 218, 169, 0.3),
                    0 0 45px rgba(115, 218, 169, 0.5);
                transform: scale(1.1);
            }
        }
    `;

    document.head.appendChild(style);
    console.log('AnimatedLoadingSkeleton: Styles injected');
}

injectSkeletonStyles();
window.AnimatedLoadingSkeleton = AnimatedLoadingSkeleton;
