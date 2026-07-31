/**
 * theme.js — Handles Dark/Light mode toggling and persistence
 */

document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const icon = themeToggleBtn?.querySelector('i');
    
    // Check local storage or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'light' || (!savedTheme && !prefersDark)) {
        document.body.setAttribute('data-theme', 'light');
        if (icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    } else {
        document.body.removeAttribute('data-theme'); // default is dark
    }

    // Toggle handler
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            if (document.body.getAttribute('data-theme') === 'light') {
                // Switch to dark
                document.body.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
                if (icon) {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                }
            } else {
                // Switch to light
                document.body.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                if (icon) {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                }
            }
            
            // Dispatch event for charts to redraw if needed
            window.dispatchEvent(new Event('themeChanged'));
        });
    }
});
