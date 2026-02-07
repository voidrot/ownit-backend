// Open edit fallback for chores page
function openEditChore(id) {
  // navigate to same path with ?edit=<id>
  window.location.href = window.location.pathname + '?edit=' + id;
}

// expose globally for inline handlers to call
window.openEditChore = openEditChore;

// Open edit for locations: navigate with query param to request server prefill or
// fallback to client-side behavior. The server currently doesn't support
// ?edit_location= but keeping symmetry with chores allows future server-side
// handling if desired.
function openEditLocation(id) {
  // Fetch location JSON and open the quick-add location panel, prefilling fields.
  // Build endpoint relative to the current chores page path so we use the
  // same prefix that the Django app was mounted at (e.g. /portal/)
  const base = window.location.pathname.replace(/\/$/, '');
  const url = base + '/location/' + encodeURIComponent(id) + '/json/';
  fetch(url, { credentials: 'same-origin' })
    .then(resp => {
      if (!resp.ok) throw new Error('Failed to fetch location');
      return resp.json();
    })
    .then(data => {
      // Activate the 'location' quick-add tab
          const tab = document.querySelector('[role="tab"][data-tab="location"]');
          // Try to trigger the tab click for any listeners, then use the shared helper
          if (tab) tab.click();
          if (window.activateQuickAddTab && typeof window.activateQuickAddTab === 'function') {
            window.activateQuickAddTab('location');
          }

      const panel = document.querySelector('.quick-add-panel[data-panel="location"]');
      if (!panel) return;

      // Fill inputs: prefer name/description inputs by name attribute
      const nameInput = panel.querySelector('input[name="name"], input#id_name');
      const descInput = panel.querySelector('textarea[name="description"], textarea#id_description');
      const hiddenNotes = panel.querySelector('input[name="notes"]');

      if (nameInput) nameInput.value = data.name || '';
      if (descInput) descInput.value = data.description || '';
      if (hiddenNotes) hiddenNotes.value = JSON.stringify(data.notes || []);

      // Ensure hidden id field is present for update
      let idInput = panel.querySelector('input[name="id"]');
      if (!idInput) {
        idInput = document.createElement('input');
        idInput.type = 'hidden';
        idInput.name = 'id';
        panel.querySelector('form').appendChild(idInput);
      }
      idInput.value = data.id;

      // Change submit button text to indicate update
      const submitBtn = panel.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.textContent = 'Update Location';

      // If notes UI helper is present, use it to set notes; otherwise render list manually
      if (window._notesPanels && window._notesPanels['location'] && typeof window._notesPanels['location'].setNotes === 'function') {
        window._notesPanels['location'].setNotes(data.notes || []);
      } else {
        const notesList = panel.querySelector('#location-notes-list');
        if (notesList) {
          notesList.innerHTML = '';
          (data.notes || []).forEach(n => {
            const li = document.createElement('li');
            li.className = 'flex items-center justify-between';
            const span = document.createElement('span');
            span.textContent = n;
            li.appendChild(span);
            notesList.appendChild(li);
          });
        }
      }

      // Focus the name input for quick editing
      if (nameInput) nameInput.focus();
    })
    .catch(err => {
      console.error('openEditLocation error', err);
      // fallback to server-side navigation
      window.location.href = window.location.pathname + '?edit_location=' + id;
    });
}

window.openEditLocation = openEditLocation;

// Intercept the location quick-add form and submit via fetch to enable inline create/update
document.addEventListener('DOMContentLoaded', function() {
  const panel = document.querySelector('.quick-add-panel[data-panel="location"]');
  if (!panel) return;
  const form = panel.querySelector('form[action][method="post"]');
  if (!form) return;

  // helper to get CSRF token from cookie
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function clearAjaxErrors() {
    const prev = form.querySelectorAll('.ajax-error');
    prev.forEach(n => n.remove());
  }

  function renderFieldErrors(errors) {
    // errors may be either the get_json_data format or simple list strings
    Object.keys(errors).forEach(fieldName => {
      const fieldErrors = errors[fieldName];
      let messages = [];
      if (Array.isArray(fieldErrors)) {
        // fallback format: list of strings
        messages = fieldErrors;
      } else if (typeof fieldErrors === 'object' && fieldErrors.length === undefined) {
        // get_json_data format: list of objects under key
        try {
          messages = fieldErrors.map(e => e.message || JSON.stringify(e));
        } catch (e) {
          messages = [String(fieldErrors)];
        }
      } else {
        messages = [String(fieldErrors)];
      }

      // find input/textarea/select by name
      const selector = `[name="${fieldName}"]`;
      const input = form.querySelector(selector);
      const container = input ? input.parentElement : form;
      messages.forEach(msg => {
        const el = document.createElement('p');
        el.className = 'text-error text-sm mt-1 ajax-error';
        el.textContent = msg;
        container.appendChild(el);
      });
    });
  }

  function renderNonFieldErrors(errors) {
    if (!errors || !errors.__all__) return;
    const msgs = errors.__all__;
    const wrapper = document.createElement('div');
    wrapper.className = 'alert alert-error mb-2 ajax-error';
    const ul = document.createElement('ul');
    ul.className = 'list-disc list-inside';
    msgs.forEach(m => {
      const li = document.createElement('li');
      li.textContent = m.message || m;
      ul.appendChild(li);
    });
    wrapper.appendChild(ul);
    form.insertBefore(wrapper, form.firstChild);
  }

  function buildLocationCard(loc) {
    // Create a DOM element matching template structure for a single location card
    const outer = document.createElement('div');
    outer.className = 'collapse card bg-base-100 shadow-sm rounded-lg mb-3';

    const inputId = 'collapse-location-' + loc.id;
    const input = document.createElement('input');
    input.id = inputId;
    input.type = 'checkbox';
    input.className = 'sr-only';
    outer.appendChild(input);

    const label = document.createElement('label');
    label.setAttribute('for', inputId);
    label.className = 'collapse-title p-0 cursor-pointer';
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body flex items-center justify-between p-4';
    const left = document.createElement('div');
    left.className = 'flex-1 min-w-0';
    const nameHeading = document.createElement('h3');
    nameHeading.className = 'text-base font-semibold truncate mb-1';
    nameHeading.textContent = loc.name;
    const descP = document.createElement('p');
    descP.className = 'text-sm text-muted truncate';
    descP.textContent = loc.description || '—';
    left.appendChild(nameHeading);
    left.appendChild(descP);
    cardBody.appendChild(left);

    const right = document.createElement('div');
    right.className = 'flex items-center gap-2';
    const editA = document.createElement('a');
    editA.href = '#';
    editA.className = 'btn btn-sm btn-ghost';
    editA.textContent = 'Edit';
    editA.addEventListener('click', function(e) { e.preventDefault(); openEditLocation(loc.id); });
    right.appendChild(editA);

    const delForm = document.createElement('form');
    delForm.method = 'post';
    // make delete action relative to current chores base path
    const basePath = window.location.pathname.replace(/\/$/, '');
    delForm.action = basePath + '/location/' + encodeURIComponent(loc.id) + '/delete/';
    delForm.className = 'inline';
    delForm.onsubmit = function() { return confirm('Delete this location?'); };
    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    // Try to reuse existing csrf token value from page
    const existingCsrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (existingCsrf) csrf.value = existingCsrf.value;
    delForm.appendChild(csrf);
    const delBtn = document.createElement('button');
    delBtn.type = 'submit';
    delBtn.className = 'btn btn-sm btn-error';
    delBtn.textContent = 'Delete';
    delForm.appendChild(delBtn);
    right.appendChild(delForm);

    cardBody.appendChild(right);
    label.appendChild(cardBody);
    outer.appendChild(label);

    const content = document.createElement('div');
    content.className = 'collapse-content p-0';
    const body2 = document.createElement('div');
    body2.className = 'card-body';
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';
    const d1 = document.createElement('div');
    const h3a = document.createElement('h3');
    h3a.className = 'font-semibold';
    h3a.textContent = 'Description';
    const p1 = document.createElement('p');
    p1.className = 'text-sm';
    p1.textContent = loc.description || '—';
    d1.appendChild(h3a);
    d1.appendChild(p1);
    const d2 = document.createElement('div');
    const h3b = document.createElement('h3');
    h3b.className = 'font-semibold';
    h3b.textContent = 'Notes';
    d2.appendChild(h3b);
    if (loc.notes && loc.notes.length) {
      const ul = document.createElement('ul');
      ul.className = 'list-disc list-inside text-sm';
      loc.notes.forEach(n => {
        const li = document.createElement('li');
        li.textContent = n;
        ul.appendChild(li);
      });
      d2.appendChild(ul);
    } else {
      const p2 = document.createElement('p');
      p2.className = 'text-sm';
      p2.textContent = '—';
      d2.appendChild(p2);
    }
    grid.appendChild(d1);
    grid.appendChild(d2);
    body2.appendChild(grid);
    content.appendChild(body2);
    outer.appendChild(content);

    return outer;
  }

  function upsertLocationCard(loc) {
    // find locations container
    const listContainer = document.querySelector('#collapse-locations-toggle').closest('.collapse').querySelector('.collapse-content .p-4');
    if (!listContainer) return;
    // try find existing card by input id
    const existing = listContainer.querySelector('#collapse-location-' + loc.id);
    if (existing) {
      // existing is the input; walk to outer card
      const outer = existing.closest('.collapse.card');
      if (outer) {
        const newEl = buildLocationCard(loc);
        outer.replaceWith(newEl);
        return;
      }
    }
    // insert new at top
    const newCard = buildLocationCard(loc);
    // add to top of p-4 container
    listContainer.insertBefore(newCard, listContainer.firstChild);
  }

  form.addEventListener('submit', function(ev) {
    ev.preventDefault();
    clearAjaxErrors();

    // ensure notes hidden input is synced if notes ui exists
    try {
      if (window._notesPanels && window._notesPanels['location'] && typeof window._notesPanels['location'].getNotes === 'function') {
        const notes = window._notesPanels['location'].getNotes() || [];
        const hiddenNotes = form.querySelector('input[name="notes"]');
        if (hiddenNotes) hiddenNotes.value = JSON.stringify(notes);
      }
    } catch (e) {
      console.warn('notes sync failed', e);
    }

    const action = form.getAttribute('action') || window.location.href;
    const fd = new FormData(form);
    fetch(action, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: fd
    })
    .then(resp => resp.json().then(j => ({status: resp.status, body: j})))
    .then(({status, body}) => {
      if (status >= 200 && status < 300 && body && body.success) {
        // update DOM with returned location
        upsertLocationCard(body.location);
        // clear form
        form.reset();
        // explicitly clear name/description/notes in case custom UI keeps values
        const nameInput = form.querySelector('input[name="name"], input#id_name');
        const descInput = form.querySelector('textarea[name="description"], textarea#id_description');
        const hiddenNotes = form.querySelector('input[name="notes"]');
        if (nameInput) nameInput.value = '';
        if (descInput) descInput.value = '';
        if (hiddenNotes) hiddenNotes.value = JSON.stringify([]);
        // remove hidden id input and restore submit button text
        const idHidden = form.querySelector('input[name="id"]');
        if (idHidden) idHidden.remove();
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.textContent = 'Add Location';
        // clear notes UI/list
        if (window._notesPanels && window._notesPanels['location'] && typeof window._notesPanels['location'].clear === 'function') {
          window._notesPanels['location'].clear();
        }
        const notesList = form.querySelector('#location-notes-list');
        if (notesList) notesList.innerHTML = '';
        // optionally collapse the locations section open so user sees new/updated
        const locToggle = document.getElementById('collapse-locations-toggle');
        if (locToggle && !locToggle.checked) locToggle.checked = true;
      } else if (body && body.errors) {
        renderNonFieldErrors(body.errors);
        renderFieldErrors(body.errors);
      } else {
        // unknown error — fallback to full reload
        window.location.reload();
      }
    })
    .catch(err => {
      console.error('Location AJAX save failed', err);
      window.location.reload();
    });
  });
});
