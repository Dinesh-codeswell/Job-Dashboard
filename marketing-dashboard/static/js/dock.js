/**
 * FloatingDock-style navigation (vanilla JS)
 * - Desktop: circular icon dock whose items grow as the cursor approaches them
 *   (spring-eased via requestAnimationFrame), with hover tooltips.
 * - Mobile: a circular toggle that expands/collapses the nav items above it.
 */
(function () {
    'use strict';

    const bar = document.getElementById('dockBar');

    // ========================================================================
    // Desktop: cursor-following scale (springy)
    // ========================================================================
    if (bar) {
        const items = [...bar.querySelectorAll('.dock-item')];
        const BASE = 40;    // base item size (px)
        const GROW = 76;    // max item size when the cursor is on it
        const RADIUS = 160; // influence radius around each item (px)
        const MAX_DIST = 420; // mouse must be within this of the bar to matter

        let current = items.map(() => 1);   // rendered scale
        let target = items.map(() => 1);    // desired scale
        let rafId = null;
        let mouseX = -9999;
        let mouseY = -9999;

        function tick() {
            let animating = false;
            items.forEach((el, i) => {
                if (Math.abs(target[i] - current[i]) > 0.001) {
                    // Ease current toward target (feels springy)
                    current[i] += (target[i] - current[i]) * 0.16;
                    animating = true;
                }
                el.style.transform = `scale(${current[i]})`;
            });
            if (animating) {
                rafId = requestAnimationFrame(tick);
            } else {
                rafId = null;
            }
        }

        function startAnim() {
            if (!rafId) rafId = requestAnimationFrame(tick);
        }

        function updateTargets() {
            const rect = bar.getBoundingClientRect();
            const barCx = rect.left + rect.width / 2;
            const barCy = rect.top + rect.height / 2;
            const distToBar = Math.hypot(mouseX - barCx, mouseY - barCy);

            if (distToBar > MAX_DIST) {
                target = items.map(() => 1);
                return;
            }

            items.forEach((el, i) => {
                const r = el.getBoundingClientRect();
                const cx = r.left + r.width / 2;
                const cy = r.top + r.height / 2;
                const d = Math.hypot(mouseX - cx, mouseY - cy);
                const t = Math.max(0, 1 - d / RADIUS);
                target[i] = 1 + t * (GROW / BASE - 1);
            });
        }

        bar.addEventListener('mousemove', (e) => {
            mouseX = e.pageX;
            mouseY = e.pageY;
            updateTargets();
            startAnim();
        });

        bar.addEventListener('mouseleave', () => {
            target = items.map(() => 1);
            startAnim();
        });
    }

    // ========================================================================
    // Mobile: expand / collapse toggle
    // ========================================================================
    const toggle = document.getElementById('dockMobileToggle');
    const menu = document.getElementById('dockMobileMenu');

    if (toggle && menu) {
        const setOpen = (open) => {
            menu.classList.toggle('open', open);
            toggle.classList.toggle('open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            const icon = toggle.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = open ? 'close' : 'menu';
        };

        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            setOpen(!menu.classList.contains('open'));
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dock-mobile')) {
                setOpen(false);
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') setOpen(false);
        });

        // Close after picking an item
        menu.addEventListener('click', () => setOpen(false));
    }
})();
