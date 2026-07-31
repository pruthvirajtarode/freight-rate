/**
 * december.js — Logic for fetching and rendering the December predictions chart
 * Uses Chart.js via CDN (or Plotly) for interactive rendering.
 */

document.addEventListener('DOMContentLoaded', async () => {
    const apiBase = typeof API_BASE === 'string' ? API_BASE : '/api/v1';
    const ctx = document.getElementById('decemberChart');
    if (!ctx) return;
    
    try {
        // Since we don't have a direct JSON endpoint for december chart yet, 
        // in a real app we'd fetch the generated CSV or a JSON endpoint.
        // For demonstration, we will assume we can fetch the CSV directly or 
        // the backend exposes it. 
        // If not, we instruct the user to download the generated CSV.
        
        const dlBtn = document.getElementById('download-dec-btn');
        if (dlBtn) {
            dlBtn.href = `${apiBase}/download/december`;
        }
        
    } catch (error) {
        console.error("Failed to load December chart logic", error);
    }
});
