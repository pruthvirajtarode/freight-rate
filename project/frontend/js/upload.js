/**
 * upload.js — Handles drag & drop CSV upload for batch predictions
 * Enhanced with upload progress, summary stats card, and toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('csv-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const statusText = document.getElementById('upload-status');
    const resultsContainer = document.getElementById('upload-results-container');
    const resultsTableBody = document.querySelector('#upload-results-table tbody');

    if (!dropZone || !fileInput) return;

    // ---- Drag & Drop ----
    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
        dropZone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); }, false);
    });
    ['dragenter', 'dragover'].forEach(ev => {
        dropZone.addEventListener(ev, () => dropZone.classList.add('highlight'), false);
    });
    ['dragleave', 'drop'].forEach(ev => {
        dropZone.addEventListener(ev, () => dropZone.classList.remove('highlight'), false);
    });

    dropZone.addEventListener('drop', e => handleFiles(e.dataTransfer.files));
    fileInput.addEventListener('change', function () { handleFiles(this.files); });

    let currentFile = null;

    function handleFiles(files) {
        if (!files.length) return;
        const file = files[0];

        if (!file.name.toLowerCase().endsWith('.csv')) {
            showStatus('❌ Please upload a valid .csv file.', 'error');
            showToast('Invalid File', 'Only CSV files are supported for batch prediction.', 'error');
            return;
        }

        currentFile = file;
        const sizeKB = (file.size / 1024).toFixed(1);
        showStatus(`📄 ${file.name} (${sizeKB} KB) — Ready to process`, 'info');
        uploadBtn.disabled = false;

        // Update drop zone visual
        dropZone.innerHTML = `
            <i class="fas fa-file-csv" style="font-size:2.5rem;color:var(--success);margin-bottom:0.75rem;"></i>
            <h3 style="color:var(--success);">${file.name}</h3>
            <p class="text-muted">${sizeKB} KB · Ready to process</p>
            <input type="file" id="csv-upload" accept=".csv" style="display:none;">
        `;
        // Re-bind after re-render
        const newInput = document.getElementById('csv-upload');
        if (newInput) newInput.addEventListener('change', function () { handleFiles(this.files); });
    }

    uploadBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        const originalBtnHTML = uploadBtn.innerHTML;
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        showStatus('⚙️ Uploading and running batch prediction...', 'info');

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            const response = await fetch('/api/v1/predict/batch', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                let msg = err.detail || 'Upload failed';
                if (Array.isArray(msg)) {
                    msg = msg.map(e => e.msg ?? JSON.stringify(e)).join(', ');
                }
                throw new Error(msg);
            }

            const result = await response.json();
            showStatus(`✅ ${result.data.length} rows predicted successfully!`, 'success');
            showToast('Batch Complete', `${result.data.length} loads predicted successfully.`, 'success');
            renderResults(result.data);

        } catch (error) {
            showStatus(`❌ ${error.message}`, 'error');
            showToast('Prediction Failed', error.message, 'error');
            uploadBtn.disabled = false;
        } finally {
            uploadBtn.innerHTML = originalBtnHTML;
        }
    });

    function showStatus(message, type) {
        if (!statusText) return;
        statusText.textContent = message;
        statusText.className = `status-text ${type}`;
    }

    function renderResults(data) {
        if (!resultsContainer || !resultsTableBody || !data || !data.length) return;

        // ---- Compute summary stats ----
        const rates = data.map(r => parseFloat(r.predicted_rate) || 0).filter(r => r > 0);
        const avg   = rates.reduce((a, b) => a + b, 0) / rates.length;
        const max   = Math.max(...rates);
        const min   = Math.min(...rates);
        const total = rates.reduce((a, b) => a + b, 0);

        // ---- Inject summary banner above table ----
        const existing = document.getElementById('batch-summary');
        if (existing) existing.remove();

        const summary = document.createElement('div');
        summary.id = 'batch-summary';
        summary.style.cssText = `
            display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;
            margin-bottom:1.5rem;
        `;
        summary.innerHTML = `
            ${statBox('Total Loads', data.length, 'fas fa-boxes', '#818CF8')}
            ${statBox('Avg Rate', '$' + avg.toFixed(2), 'fas fa-chart-line', '#34D399')}
            ${statBox('Max Rate', '$' + max.toFixed(2), 'fas fa-arrow-up', '#FCD34D')}
            ${statBox('Min Rate', '$' + min.toFixed(2), 'fas fa-arrow-down', '#F87171')}
        `;
        resultsContainer.querySelector('.chart-header, div:first-child')
            ?.insertAdjacentElement('afterend', summary)
            ?? resultsContainer.prepend(summary);

        // ---- Populate table (first 50 rows) ----
        resultsTableBody.innerHTML = '';
        const displayData = data.slice(0, 50);

        displayData.forEach((row, idx) => {
            const tr = document.createElement('tr');
            const id       = row.load_id || `#${idx + 1}`;
            const pickup   = row.pickup   || '—';
            const delivery = row.delivery || '—';
            const rate     = row.predicted_rate != null ? parseFloat(row.predicted_rate) : null;
            const rateStr  = rate != null ? `$${rate.toFixed(2)}` : '—';
            const rateColor = rate > avg ? '#34D399' : rate < avg ? '#F87171' : '#94A3B8';

            tr.innerHTML = `
                <td style="font-weight:600;font-family:'Outfit',sans-serif;">${id}</td>
                <td>${pickup}</td>
                <td>${delivery}</td>
                <td style="color:${rateColor};font-weight:700;font-family:'Outfit',sans-serif;">${rateStr}</td>
            `;
            resultsTableBody.appendChild(tr);
        });

        if (data.length > 50) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="4" style="text-align:center;color:var(--text-muted);padding:1rem;font-style:italic;">
                Showing first 50 of ${data.length} results. Download the CSV for the full dataset.
            </td>`;
            resultsTableBody.appendChild(tr);
        }

        resultsContainer.style.display = 'block';
        setTimeout(() => resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    }

    function statBox(label, value, icon, color) {
        return `
            <div style="background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:var(--radius-md);padding:1.25rem;backdrop-filter:blur(12px);text-align:center;">
                <i class="${icon}" style="font-size:1.4rem;color:${color};margin-bottom:0.5rem;display:block;"></i>
                <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;letter-spacing:-0.03em;">${value}</div>
                <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem;">${label}</div>
            </div>`;
    }
});

// ===== TOAST NOTIFICATION HELPER =====
function showToast(title, message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success:'fa-check-circle', error:'fa-times-circle', info:'fa-info-circle', warning:'fa-exclamation-triangle' };

    const toast = document.createElement('div');
    toast.className = `toast ${type} toast-enter`;
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info} toast-icon"></i>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-msg">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 350);
    }, duration);
}
