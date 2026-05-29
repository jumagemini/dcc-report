(function() {
  'use strict';
  console.log('[OfflineHandler] Script loaded (simplified).');

  const form = document.querySelector('.form-container form');
  if (!form) {
    console.warn('[OfflineHandler] No institution form found – exiting.');
    return;
  }
  console.log('[OfflineHandler] Form detected, binding single submit listener.');

  // Use a flag to prevent multiple submissions
  let saving = false;

  // Helper: fully reset the form, including QTY spans, signature, and previews
  function resetFormCompletely() {
    // Reset native form fields
    form.reset();

    // Reset QTY displays
    document.querySelectorAll('#device-table tbody tr').forEach(row => {
      const qtySpan = row.querySelector('.qty-display');
      const isRequired = row.dataset.required === 'true';
      if (qtySpan) {
        qtySpan.textContent = isRequired ? '1' : 'N/A';
      }
    });

    // Reset preview spans (contractor, rep, date)
    const companySpan = document.getElementById('preview-company');
    const repSpan = document.getElementById('preview-rep');
    const dateSpan = document.getElementById('preview-date');
    if (companySpan) companySpan.textContent = '';
    if (repSpan) repSpan.textContent = '';
    if (dateSpan) dateSpan.textContent = '';

    // Reset signature canvas and hidden field
    const canvas = document.getElementById('signature-canvas');
    if (canvas && typeof SignaturePad !== 'undefined') {
      // SignaturePad instance is not stored globally; clearing the canvas is enough
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    const sigInput = document.getElementById('signature-image-data');
    if (sigInput) sigInput.value = '';
  }

  form.addEventListener('submit', async function(e) {
    if (navigator.onLine) return;           // online → normal AJAX submission
    if (saving) return;                     // already processing an offline save

    e.preventDefault();
    saving = true;
    console.log('[OfflineHandler] Offline – saving form data...');

    try {
      const formData = new FormData(form);
      const url = form.action;
      const headers = {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken') || '',
        'X-Requested-With': 'XMLHttpRequest'
      };

      // Build URL‑encoded body, skipping file fields
      const bodyParams = new URLSearchParams();
      for (const [key, value] of formData.entries()) {
        if (value instanceof File) continue;
        bodyParams.append(key, value);
      }
      const bodyBlob = new Blob([bodyParams.toString()], { type: 'application/x-www-form-urlencoded' });
      const requestPayload = { url, body: bodyBlob, headers };

      // Store request
      const db = await window.openOfflineDB();
      const txReq = db.transaction('pending-requests', 'readwrite');
      await txReq.objectStore('pending-requests').add(requestPayload);
      await txReq.done;

      // Store metadata
      const metadata = {
        institutionName: formData.get('name') || 'Unknown',
        dccName: formData.get('dcc_name') || 'Unknown',
        timestamp: Date.now()
      };
      const txMeta = db.transaction('pending-metadata', 'readwrite');
      await txMeta.objectStore('pending-metadata').add(metadata);
      await txMeta.done;

      console.log('[OfflineHandler] Data + metadata saved.');

      // Success notification
      alert('✅ Data saved offline and will be submitted when back online.');

      // Clear the form for the next entry
      resetFormCompletely();

    } catch (error) {
      console.error('[OfflineHandler] Save failed:', error);
      alert('❌ Offline save failed. Please try again online.');
    } finally {
      saving = false;
    }
  });
})();