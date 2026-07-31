/**
 * dashboard.js — Logic for fetching metrics and populating the dashboard
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Only run on dashboard page
    if (!document.getElementById('dashboard-metrics')) return;

    try {
        // Fetch metrics from backend
        const metrics = await fetchAPI('/metrics');
        
        // Update DOM elements
        document.getElementById('kpi-best-model').innerText = metrics.best_model || 'N/A';
        document.getElementById('kpi-rmse').innerText = `$${(metrics.val_rmse || 0).toFixed(2)}`;
        document.getElementById('kpi-mae').innerText = `$${(metrics.val_mae || 0).toFixed(2)}`;
        document.getElementById('kpi-r2').innerText = (metrics.val_r2 || 0).toFixed(4);

        // Load static charts
        loadStaticChart('feature_importance.png', 'chart-feature-importance');
        loadStaticChart('residuals.png', 'chart-residuals');
        loadStaticChart('prediction_scatter.png', 'chart-scatter');

        // Fetch model comparison for table
        const comparison = await fetchAPI('/models/compare');
        populateComparisonTable(comparison);

    } catch (error) {
        console.error("Dashboard failed to load metrics. Is the backend running and trained?", error);
        // We could show a toast notification here
    }
    
    // Animate KPI cards entry
    if (typeof gsap !== 'undefined') {
        gsap.from('.kpi-card', {
            y: 30,
            opacity: 0,
            duration: 0.5,
            stagger: 0.1,
            ease: 'power2.out'
        });
    }
});

function populateComparisonTable(comparisonData) {
    const tbody = document.querySelector('#comparison-table tbody');
    if (!tbody || !comparisonData) return;

    tbody.innerHTML = '';
    
    // Convert to array and sort by RMSE
    const models = Object.keys(comparisonData).map(key => ({
        name: key,
        ...comparisonData[key]
    })).sort((a, b) => a.rmse - b.rmse);

    models.forEach((model, index) => {
        const isBest = index === 0;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <strong>${model.name}</strong>
                ${isBest ? '<span class="badge badge-success" style="margin-left: 8px;">Best</span>' : ''}
            </td>
            <td>$${model.rmse.toFixed(2)}</td>
            <td>$${model.mae.toFixed(2)}</td>
            <td>${model.r2.toFixed(4)}</td>
            <td>${model.fit_time_seconds.toFixed(2)}s</td>
        `;
        tbody.appendChild(tr);
    });
}
