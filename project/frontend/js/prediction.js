/**
 * prediction.js — Logic for single prediction form submission
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('single-predict-form');
    const resultBox = document.getElementById('prediction-result-box');
    const resultValue = document.getElementById('prediction-result-value');
    
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Gather form data
        const formData = new FormData(form);
        const data = {
            pickup: formData.get('pickup'),
            delivery: formData.get('delivery'),
            distance: parseFloat(formData.get('distance')),
            equipment: formData.get('equipment'),
            weight: parseFloat(formData.get('weight')),
            date: formData.get('date'),
            pickup_lat: parseFloat(formData.get('pickup_lat')) || 0,
            pickup_lon: parseFloat(formData.get('pickup_lon')) || 0,
            delivery_lat: parseFloat(formData.get('delivery_lat')) || 0,
            delivery_lon: parseFloat(formData.get('delivery_lon')) || 0,
            market_index: parseFloat(formData.get('market_index')) || null,
            quote_signal: parseFloat(formData.get('quote_signal')) || null
        };
        
        // Show loading state
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Predicting...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/v1/predict/single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const err = await response.json();
                let errorMsg = err.detail || 'Prediction failed';
                if (Array.isArray(errorMsg)) {
                    // Pydantic v2 validation errors: [{loc: [...], msg: "...", type: "..."}, ...]
                    errorMsg = errorMsg.map(item => {
                        const loc = Array.isArray(item.loc) ? item.loc.join('.') : String(item.loc ?? '');
                        const msg = item.msg ?? item.message ?? JSON.stringify(item);
                        return loc ? `${loc}: ${msg}` : msg;
                    }).join('\n');
                } else if (typeof errorMsg !== 'string') {
                    errorMsg = JSON.stringify(errorMsg);
                }
                throw new Error(errorMsg);
            }
            
            const result = await response.json();
            
            // Display result
            resultValue.innerText = `$${result.predicted_rate.toFixed(2)}`;
            resultBox.style.display = 'block';

            // Hide previous API error (if any)
            const errEl = document.getElementById('api-error');
            if (errEl) errEl.style.display = 'none';
            
            // Animation
            if (typeof gsap !== 'undefined') {
                gsap.from(resultBox, { scale: 0.9, opacity: 0, duration: 0.4, ease: 'back.out(1.7)' });
            }
            
        } catch (error) {
            const errEl = document.getElementById('api-error');
            if (errEl) {
                errEl.textContent = `Error: ${error.message}`;
                errEl.className = 'status-text error';
                errEl.style.display = 'block';
            } else {
                console.error('Prediction error:', error);
            }
        } finally {
            // Restore button
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
});
