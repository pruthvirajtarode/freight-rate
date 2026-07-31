/**
 * main.js — Shared initialization (Particles, GSAP, basic routing)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Initialize Particles.js background if element exists
    if (document.getElementById('particles-js')) {
        // We'll use a simple config for a subtle animated background
        try {
            particlesJS('particles-js', {
                "particles": {
                    "number": { "value": 40, "density": { "enable": true, "value_area": 800 } },
                    "color": { "value": "#6366F1" },
                    "shape": { "type": "circle" },
                    "opacity": { "value": 0.3, "random": true },
                    "size": { "value": 3, "random": true },
                    "line_linked": { "enable": true, "distance": 150, "color": "#6366F1", "opacity": 0.2, "width": 1 },
                    "move": { "enable": true, "speed": 1, "direction": "none", "random": true, "out_mode": "out" }
                },
                "interactivity": {
                    "detect_on": "canvas",
                    "events": {
                        "onhover": { "enable": true, "mode": "grab" },
                        "onclick": { "enable": true, "mode": "push" },
                        "resize": true
                    },
                    "modes": {
                        "grab": { "distance": 140, "line_linked": { "opacity": 0.5 } },
                        "push": { "particles_nb": 2 }
                    }
                },
                "retina_detect": true
            });
        } catch (e) {
            console.warn('Particles.js not loaded or failed to init.', e);
        }
    }

    // Set active nav link based on current path
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    const navToggle = document.getElementById('nav-toggle-btn');
    const navLinks = document.getElementById('nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            const isOpen = navLinks.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });

        document.addEventListener('click', (event) => {
            if (!navToggle.contains(event.target) && !navLinks.contains(event.target)) {
                navLinks.classList.remove('open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Initialize GSAP animations if available
    if (typeof gsap !== 'undefined') {
        gsap.from('.nav-brand', { opacity: 0, y: -20, duration: 0.6, ease: 'power2.out' });
        gsap.from('.nav-link', { opacity: 0, y: -20, duration: 0.6, stagger: 0.1, ease: 'power2.out', delay: 0.2 });
    }
});

// Helper for API calls
const API_BASE = "/api/v1";

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`API returned non-JSON response: ${text.slice(0,200)}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Fetch failed:', error);
        throw error;
    }
}
