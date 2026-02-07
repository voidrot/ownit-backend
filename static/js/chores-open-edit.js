// Open edit fallback for chores page
function openEditChore(id) {
  // navigate to same path with ?edit=<id>
  window.location.href = window.location.pathname + '?edit=' + id;
}

// expose globally for inline handlers to call
window.openEditChore = openEditChore;

// Helper: clear and render AJAX form errors safely.
function clearAjaxErrors() {
  try {
    // remove any previous non-field error blocks added by AJAX
    document.querySelectorAll('.ajax-nonfield-errors').forEach(el => el.remove());
    // remove any previous field-level AJAX error nodes
    document.querySelectorAll('.ajax-field-error').forEach(el => el.remove());
  } catch (e) { /* ignore */ }
}

function renderNonFieldErrors(errors) {
  try {
    const panel = document.querySelector('.quick-add-panel:not(.hidden)') || document.querySelector('.quick-add-panel');
    if (!panel) return;
    const msgs = [];
    if (Array.isArray(errors)) {
      errors.forEach(m => msgs.push(m.message || m));
    } else if (errors && typeof errors === 'object') {
      if (errors.__all__) (errors.__all__ || []).forEach(m => msgs.push(m.message || m));
      if (errors.non_field_errors) (errors.non_field_errors || []).forEach(m => msgs.push(m.message || m));
    }
    if (!msgs.length) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'alert alert-error mb-2 ajax-nonfield-errors';
    const ul = document.createElement('ul'); ul.className = 'list-disc list-inside';
    msgs.forEach(m => { const li = document.createElement('li'); li.textContent = m; ul.appendChild(li); });
    wrapper.appendChild(ul);
    panel.insertBefore(wrapper, panel.firstChild);
  } catch (e) { console.warn('renderNonFieldErrors failed', e); }
}

function renderFieldErrors(errors) {
  try {
    const panel = document.querySelector('.quick-add-panel:not(.hidden)') || document.querySelector('.quick-add-panel');
    if (!panel || !errors) return;
    Object.keys(errors).forEach(field => {
      if (field === '__all__' || field === 'non_field_errors') return;
      const input = panel.querySelector('[name="' + field + '"]');
      if (!input) return;
      const msgs = Array.isArray(errors[field]) ? errors[field].map(m => m.message || m).join(' ') : (errors[field].message || errors[field]);
      const p = document.createElement('p');
      p.className = 'text-error text-sm mt-1 ajax-field-error';
      p.textContent = msgs;
      input.insertAdjacentElement('afterend', p);
    });
  } catch (e) { console.warn('renderFieldErrors failed', e); }
}

// Simple cookie helper to read CSRF token; fallback used by AJAX submitters.
function getCookie(name) {
  try {
    const matches = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/\+^])/g, '\\$1') + '=([^;]*)'));
    return matches ? decodeURIComponent(matches[1]) : null;
  } catch (e) {
    return null;
  }
}

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
      window.location.href = window.location.pathname + '?edit_location=' + id;
    });
}

// --- Task helpers / handlers (moved out of renderNonFieldErrors so they're always available) ---
// delegated click handler for task edit links
document.addEventListener('click', function(evt) {
  const a = evt.target.closest && evt.target.closest('a[data-action="open-edit-task"]');
  if (!a) return;
  evt.preventDefault();
  const id = a.getAttribute('data-task-id');
  if (id) {
    try { openEditTask(id); } catch (e) { console.error('openEditTask call failed', e); }
  }
});

function openEditTask(id) {
  const base = window.location.pathname.replace(/\/?$/, '');
  const url = base + '/task/' + encodeURIComponent(id) + '/json/';
  fetch(url, { credentials: 'same-origin' })
    .then(resp => {
      if (!resp.ok) throw new Error('Failed to fetch task');
      return resp.json();
    })
    .then(data => {
      if (window.activateQuickAddTab && typeof window.activateQuickAddTab === 'function') {
        window.activateQuickAddTab('task');
      } else {
        const tab = document.querySelector('[role="tab"][data-tab="task"]');
        if (tab) tab.click();
      }

      const panel = document.querySelector('.quick-add-panel[data-panel="task"]');
      if (!panel) return;

      const nameInput = panel.querySelector('input[name="name"], input#id_name');
                  const descInput = panel.querySelector('textarea[name="description"], textarea#id_description');
                  const hiddenNotes = panel.querySelector('input[name="notes"]');
                  const hiddenSteps = panel.querySelector('input[name="steps"], textarea[name="steps"]');

                  if (nameInput) nameInput.value = data.name || '';
                  if (descInput) descInput.value = data.description || '';
                  // Prefer to let the shared steps UI manage rendering and hidden value
                  // so state remains consistent. If the steps UI is available, use
                  // its API to populate steps and mark them as persisted (existing).
                  if (window._taskStepsUI && typeof window._taskStepsUI.setSteps === 'function') {
                    // When loading an existing task for edit, show ordering and
                    // remove controls so the user can modify the steps.
                    window._taskStepsUI.setSteps(data.steps || [], { persisted: false });
                  } else {
                    if (hiddenSteps) hiddenSteps.value = JSON.stringify(data.steps || []);
                    // fallback: populate DOM list if the steps UI isn't present
                    const stepsList = panel.querySelector('#task-steps-list');
                    if (stepsList) {
                      stepsList.innerHTML = '';
                      (data.steps || []).forEach(s => {
                        const li = document.createElement('li'); li.className = 'mb-1';
                        const title = document.createElement('div'); title.className = 'font-semibold'; title.textContent = s.name || '';
                        const desc = document.createElement('div'); desc.className = 'text-sm text-muted'; desc.textContent = s.description || '';
                        li.appendChild(title); if (s.description) li.appendChild(desc);
                        stepsList.appendChild(li);
                      });
                    }
                  }
                  if (hiddenNotes) hiddenNotes.value = JSON.stringify(data.notes || []);

                  let idInput = panel.querySelector('input[name="id"]');
                  if (!idInput) {
                    idInput = document.createElement('input');
                    idInput.type = 'hidden';
                    idInput.name = 'id';
                    panel.querySelector('form').appendChild(idInput);
                  }
                  idInput.value = data.id;

                  const submitBtn = panel.querySelector('button[type="submit"]');
                  if (submitBtn) submitBtn.textContent = 'Update Task';

                  // set notes UI if present
                  if (window._notesPanels && window._notesPanels['task'] && typeof window._notesPanels['task'].setNotes === 'function') {
                    window._notesPanels['task'].setNotes(data.notes || []);
                  } else {
                    const notesList = panel.querySelector('#task-notes-list');
                    if (notesList) {
                      notesList.innerHTML = '';
                      (data.notes || []).forEach(n => {
                        const li = document.createElement('li'); li.textContent = n; notesList.appendChild(li);
                      });
                    }
                  }

                  // Steps are handled above via the shared steps UI; nothing further.

                  if (nameInput) nameInput.focus();
                  // Populate equipment checkbox selections when editing a task
                  try {
                    const eqList = data.equipment || [];
                    const ids = eqList.map(function(i){
                      if (typeof i === 'object') return (i.id || '').toString();
                      return String(i);
                    });
                    const panelEq = panel.querySelectorAll('.task-equipment-checkbox');
                    if (panelEq && panelEq.length) {
                      panelEq.forEach(function(cb){ cb.checked = ids.indexOf(String(cb.value)) !== -1; });
                    }
                  } catch (e) { console.warn('task equipment populate failed', e); }
                })
                .catch(err => {
                  console.error('openEditTask error', err);
                  window.location.href = window.location.pathname + '?edit_task=' + id;
                });
            }

            window.openEditTask = openEditTask;

            function buildTaskCard(t) {
              const outer = document.createElement('div');
              outer.className = 'collapse card bg-base-100 shadow-sm rounded-lg mb-3';
              outer.id = 'task-card-' + t.id;
              const inputId = 'collapse-task-' + t.id;
              const input = document.createElement('input');
              input.id = inputId;
              input.type = 'checkbox';
              input.className = 'sr-only';
              outer.appendChild(input);

              const label = document.createElement('label');
              label.setAttribute('for', inputId);
              label.className = 'collapse-title flex items-start justify-between gap-4 cursor-pointer p-4';

              const left = document.createElement('div'); left.className = 'flex-1';
              const h = document.createElement('div'); h.className = 'font-semibold'; h.textContent = t.name || '';
              const p = document.createElement('div'); p.className = 'text-sm text-muted'; p.textContent = t.description || '';
              left.appendChild(h); left.appendChild(p);
              label.appendChild(left);

              const right = document.createElement('div'); right.className = 'flex items-center gap-2';
              const editA = document.createElement('a'); editA.href = '#'; editA.className = 'btn btn-ghost btn-sm'; editA.textContent = 'Edit';
              editA.setAttribute('data-action', 'open-edit-task'); editA.setAttribute('data-task-id', t.id);
              editA.addEventListener('click', function(e){ e.stopPropagation(); e.preventDefault(); openEditTask(t.id); });
              right.appendChild(editA);

              // Delete as POST form to avoid GET method issues. Stop propagation so clicking the button
              // doesn't toggle the collapse label.
              const delForm = document.createElement('form');
              delForm.method = 'post';
              const basePath = window.location.pathname.replace(/\/$/, '');
              delForm.action = basePath + '/task/' + encodeURIComponent(t.id) + '/delete/';
              delForm.className = 'inline';
              delForm.onsubmit = function(e) { e.stopPropagation(); return confirm('Delete this task?'); };
              const csrf = document.createElement('input'); csrf.type = 'hidden'; csrf.name = 'csrfmiddlewaretoken';
              const existingCsrf = document.querySelector('input[name="csrfmiddlewaretoken"]'); if (existingCsrf) csrf.value = existingCsrf.value;
              delForm.appendChild(csrf);
              const delBtn = document.createElement('button'); delBtn.type = 'submit'; delBtn.className = 'btn btn-ghost btn-sm text-error'; delBtn.textContent = 'Delete';
              delBtn.addEventListener('click', function(e){ e.stopPropagation(); });
              delForm.appendChild(delBtn);
              right.appendChild(delForm);
              label.appendChild(right);
              outer.appendChild(label);

              const content = document.createElement('div'); content.className = 'collapse-content p-0';
              const body = document.createElement('div'); body.className = 'card-body';
              const grid = document.createElement('div'); grid.className = 'grid md:grid-cols-3 gap-4';

              const leftCol = document.createElement('div'); leftCol.className = 'md:col-span-2';
              if (t.description) {
                const hdesc = document.createElement('h3'); hdesc.className = 'font-medium'; hdesc.textContent = 'Description';
                const pdesc = document.createElement('p'); pdesc.className = 'text-sm text-muted'; pdesc.textContent = t.description;
                leftCol.appendChild(hdesc); leftCol.appendChild(pdesc);
              }
              if (t.steps && t.steps.length) {
                const hsteps = document.createElement('h3'); hsteps.className = 'font-medium mt-4'; hsteps.textContent = 'Steps';
                const ul = document.createElement('ul'); ul.className = 'list-decimal list-inside text-sm text-muted';
                t.steps.forEach(s => { const li = document.createElement('li'); li.textContent = s.name + (s.description ? (': ' + s.description) : ''); ul.appendChild(li); });
                leftCol.appendChild(hsteps); leftCol.appendChild(ul);
              }
              // equipment will be rendered in the notes column (right) to match template layout
              grid.appendChild(leftCol);

              const notesCol = document.createElement('div'); notesCol.className = 'md:col-span-1';
              // Render equipment above notes
              if (t.equipment && t.equipment.length) {
                const heq = document.createElement('h3'); heq.className = 'font-medium'; heq.textContent = 'Equipment'; notesCol.appendChild(heq);
                const peq = document.createElement('p'); peq.className = 'text-sm text-muted mb-3';
                t.equipment.forEach(function(eq){ const span = document.createElement('span'); span.className = 'badge badge-outline mr-1'; span.textContent = (eq.name || (eq.title || eq)); peq.appendChild(span); });
                notesCol.appendChild(peq);
              }
              const hnotes = document.createElement('h3'); hnotes.className = 'font-medium'; hnotes.textContent = 'Notes'; notesCol.appendChild(hnotes);
              if (t.notes && t.notes.length) {
                const ul = document.createElement('ul'); ul.className = 'list-disc list-inside text-sm text-muted';
                t.notes.forEach(n => { const li = document.createElement('li'); li.textContent = n; ul.appendChild(li); });
                notesCol.appendChild(ul);
              } else {
                const pempty = document.createElement('div'); pempty.className = 'text-sm text-muted'; pempty.textContent = 'No notes'; notesCol.appendChild(pempty);
                // Debug: log the steps payload so we can see exactly what's posted
                try {
                  const dbgHidden = taskForm.querySelector('input[name="steps"], textarea[name="steps"]');
                  if (dbgHidden) console.debug('Task submit steps payload:', dbgHidden.value);
                } catch (e) { /* ignore */ }
              }
              grid.appendChild(notesCol);

              body.appendChild(grid);
              content.appendChild(body);
              outer.appendChild(content);
              return outer;
            }

            function upsertTaskCard(t) {
              const container = document.querySelector('#collapse-tasks-toggle').closest('.collapse').querySelector('.collapse-content .p-4');
              if (!container) return;
              const existing = container.querySelector('#task-card-' + t.id);
              if (existing) {
                const newEl = buildTaskCard(t);
                existing.replaceWith(newEl);
                return;
              }
              const newCard = buildTaskCard(t);
              container.insertBefore(newCard, container.firstChild);
            }

            window.upsertTaskCard = upsertTaskCard;

            // Task quick-add AJAX submit (save_task endpoint)
            const taskPanel = document.querySelector('.quick-add-panel[data-panel="task"]');
            if (taskPanel) {
              const taskForm = taskPanel.querySelector('form[action][method="post"]');
              if (taskForm) {
                taskForm.addEventListener('submit', function(ev) {
                  ev.preventDefault();
                  clearAjaxErrors();

                  // sync notes
                  try {
                    if (window._notesPanels && window._notesPanels['task'] && typeof window._notesPanels['task'].getNotes === 'function') {
                      const notes = window._notesPanels['task'].getNotes() || [];
                      const hiddenNotes = taskForm.querySelector('input[name="notes"]');
                      if (hiddenNotes) hiddenNotes.value = JSON.stringify(notes);
                    }
                  } catch (e) { console.warn('task notes sync failed', e); }

                  // sync steps into hidden input
                  try {
                    const stepsList = taskPanel.querySelector('#task-steps-list');
                    const hiddenSteps = taskForm.querySelector('input[name="steps"], textarea[name="steps"]');
                    if (hiddenSteps) {
                      const steps = [];
                      if (stepsList) {
                        // each li: first child text is name, second is desc optionally
                        Array.from(stepsList.children).forEach(li => {
                            // Clone the node and remove interactive controls so we don't
                            // accidentally capture button text (↑ ↓ Remove) in the title.
                            try {
                              const clone = li.cloneNode(true);
                              clone.querySelectorAll('button').forEach(b => b.remove());
                              // Try to find the step title inside the cleaned clone.
                              const titleEl = clone.querySelector('.font-semibold, .font-medium');
                              const nameText = titleEl ? titleEl.textContent : clone.textContent;
                              const descEl = clone.querySelector('.text-sm');
                              const desc = descEl ? descEl.textContent : '';
                              steps.push({ name: (nameText || '').trim(), description: (desc || '').trim() });
                            } catch (e) {
                              // Fallback to previous behavior if anything goes wrong
                              const name = li.querySelector('.font-semibold') ? li.querySelector('.font-semibold').textContent : li.textContent;
                              const descEl = li.querySelector('.text-sm');
                              const desc = descEl ? descEl.textContent : '';
                              steps.push({ name: name.trim(), description: (desc || '').trim() });
                            }
                          });
                      }
                      hiddenSteps.value = JSON.stringify(steps);
                    }
                  } catch (e) { console.warn('task steps sync failed', e); }

                  const base = window.location.pathname.replace(/\/?$/, '');
                  const action = base + '/task/save/';
                  const fd = new FormData(taskForm);
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
                      if (window.upsertTaskCard && typeof window.upsertTaskCard === 'function') window.upsertTaskCard(body.task);
                      taskForm.reset();
                      const idHidden = taskForm.querySelector('input[name="id"]'); if (idHidden) idHidden.remove();
                      const submitBtn = taskForm.querySelector('button[type="submit"]'); if (submitBtn) submitBtn.textContent = 'Add Task';
                      if (window._notesPanels && window._notesPanels['task'] && typeof window._notesPanels['task'].clear === 'function') window._notesPanels['task'].clear();
                      const notesList = taskForm.querySelector('#task-notes-list'); if (notesList) notesList.innerHTML = '';
                      const stepsList = taskForm.querySelector('#task-steps-list'); if (stepsList) stepsList.innerHTML = '';
                      const tToggle = document.getElementById('collapse-tasks-toggle'); if (tToggle && !tToggle.checked) tToggle.checked = true;
                    } else if (body && body.errors) {
                      renderNonFieldErrors(body.errors);
                      renderFieldErrors(body.errors);
                    } else {
                      window.location.reload();
                    }
                  })
                  .catch(err => { console.error('Task AJAX save failed', err); window.location.reload(); });
                });
              }
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
      grid.className = 'grid grid-cols-1 md:grid-cols-3 gap-4';

      const leftCol = document.createElement('div');
      leftCol.className = 'md:col-span-2 space-y-4';

      const dLoc = document.createElement('div');
      const hLoc = document.createElement('h3');
      hLoc.className = 'font-semibold';
      hLoc.textContent = 'Location';
      const pLoc = document.createElement('p');
      pLoc.className = 'text-sm';
      pLoc.textContent = (eq.location && (eq.location.name || eq.location)) || '—';
      dLoc.appendChild(hLoc);
      dLoc.appendChild(pLoc);
      leftCol.appendChild(dLoc);

      const dDesc = document.createElement('div');
      const hDesc = document.createElement('h3');
      hDesc.className = 'font-semibold';
      hDesc.textContent = 'Description';
      const pDesc = document.createElement('p');
      pDesc.className = 'text-sm';
      pDesc.textContent = eq.description || '—';
      dDesc.appendChild(hDesc);
      dDesc.appendChild(pDesc);
      leftCol.appendChild(dDesc);

      const dNotes = document.createElement('div');
      const hNotes = document.createElement('h3');
      hNotes.className = 'font-semibold';
      hNotes.textContent = 'Notes';
      dNotes.appendChild(hNotes);
      if (eq.notes && eq.notes.length) {
        const ul = document.createElement('ul');
        ul.className = 'list-disc list-inside text-sm';
        eq.notes.forEach(n => { const li = document.createElement('li'); li.textContent = n; ul.appendChild(li); });
        dNotes.appendChild(ul);
      } else {
        const pN = document.createElement('p'); pN.className = 'text-sm'; pN.textContent = '—'; dNotes.appendChild(pN);
      }
      grid.appendChild(leftCol);
      grid.appendChild(dNotes);
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

  // --- Equipment builders / upsert helpers (mirror template markup) ---
  function openEditEquipment(id) {
    const base = window.location.pathname.replace(/\/?$/, '');
    const url = base + '/equipment/' + encodeURIComponent(id) + '/json/';
    fetch(url, { credentials: 'same-origin' })
      .then(resp => {
        if (!resp.ok) throw new Error('Failed to fetch equipment');
        return resp.json();
      })
      .then(data => {
        if (window.activateQuickAddTab && typeof window.activateQuickAddTab === 'function') {
          window.activateQuickAddTab('equipment');
        } else {
          const tab = document.querySelector('[role="tab"][data-tab="equipment"]');
          if (tab) tab.click();
        }

        const panel = document.querySelector('.quick-add-panel[data-panel="equipment"]');
        if (!panel) return;

        const nameInput = panel.querySelector('input[name="name"], input#id_name');
        const descInput = panel.querySelector('textarea[name="description"], textarea#id_description');
        const locSelect = panel.querySelector('select[name="location"]');
        const countInput = panel.querySelector('input[name="count"]');
        const hiddenNotes = panel.querySelector('input[name="notes"]');

        if (nameInput) nameInput.value = data.name || '';
        if (descInput) descInput.value = data.description || '';
        if (countInput) countInput.value = data.count || '';
        if (hiddenNotes) hiddenNotes.value = JSON.stringify(data.notes || []);
        if (locSelect && data.location) {
          // try to select by id or name
          const opt = locSelect.querySelector('option[value="' + (data.location.id || data.location) + '"]');
          if (opt) opt.selected = true;
          else {
            // fallback: try to match by visible name
            Array.from(locSelect.options).forEach(o => { if (o.textContent.trim() === (data.location.name || data.location)) o.selected = true; });
          }
        }

        let idInput = panel.querySelector('input[name="id"]');
        if (!idInput) {
          idInput = document.createElement('input');
          idInput.type = 'hidden';
          idInput.name = 'id';
          panel.querySelector('form').appendChild(idInput);
        }
        idInput.value = data.id;

        const submitBtn = panel.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.textContent = 'Update Equipment';

        if (window._notesPanels && window._notesPanels['equipment'] && typeof window._notesPanels['equipment'].setNotes === 'function') {
          window._notesPanels['equipment'].setNotes(data.notes || []);
        } else {
          const notesList = panel.querySelector('#equipment-notes-list');
          if (notesList) {
            notesList.innerHTML = '';
            (data.notes || []).forEach(n => {
              const li = document.createElement('li');
              li.textContent = n;
              notesList.appendChild(li);
            });
          }
        }

        // Image preview / remove handling for edit flow
        try {
          const fileInput = panel.querySelector('input[type="file"][name="image"]');
          // ensure a preview container exists
          let preview = panel.querySelector('#equipment-image-preview');
          if (!preview) {
            preview = document.createElement('div');
            preview.id = 'equipment-image-preview';
            preview.className = 'mb-2';
            if (fileInput) fileInput.parentNode.insertBefore(preview, fileInput);
            else panel.querySelector('form').insertBefore(preview, panel.querySelector('form').firstChild);
          }
          preview.innerHTML = '';
          if (data.image_url) {
            const wrap = document.createElement('div');
            wrap.className = 'flex items-center gap-3';
            const img = document.createElement('img');
            img.src = data.image_url;
            img.alt = data.name || 'Equipment image';
            img.className = 'w-24 h-16 object-cover rounded';
            wrap.appendChild(img);
            const label = document.createElement('label');
            label.className = 'inline-flex items-center gap-2';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'remove_image';
            checkbox.value = '1';
            label.appendChild(checkbox);
            const span = document.createElement('span'); span.className = 'text-sm'; span.textContent = 'Remove existing image';
            label.appendChild(span);
            wrap.appendChild(label);
            preview.appendChild(wrap);
          }
        } catch (e) { console.warn('equipment image preview populate failed', e); }

        if (nameInput) nameInput.focus();
      })
      .catch(err => {
        console.error('openEditEquipment error', err);
        window.location.href = window.location.pathname + '?edit_equipment=' + id;
      });
  }

  window.openEditEquipment = openEditEquipment;

    // delegated click handler for equipment edit links (fallback for inline onclick)
    document.addEventListener('click', function(evt) {
      const a = evt.target.closest && evt.target.closest('a[data-action="open-edit-equipment"]');
      if (!a) return;
      evt.preventDefault();
      const id = a.getAttribute('data-equipment-id');
      if (id) {
        try { openEditEquipment(id); } catch (e) { console.error('openEditEquipment call failed', e); }
      }
    });

  function buildEquipmentCard(eq) {
    const outer = document.createElement('div');
    outer.className = 'collapse card bg-base-100 shadow-sm rounded-lg mb-3';

    const inputId = 'collapse-equipment-' + eq.id;
    const input = document.createElement('input');
    input.id = inputId;
    input.type = 'checkbox';
    input.className = 'sr-only';
    outer.appendChild(input);

    const label = document.createElement('label');
    label.setAttribute('for', inputId);
    label.className = 'collapse-title p-0 cursor-pointer';
    const header = document.createElement('div');
    header.className = 'flex items-center justify-between gap-4 p-4';

    const left = document.createElement('div');
    left.className = 'flex-1 min-w-0';
    const nameHeading = document.createElement('h3');
    nameHeading.className = 'text-base font-semibold truncate mb-1';
    nameHeading.textContent = eq.name;
    const descP = document.createElement('p');
    descP.className = 'text-sm text-muted truncate';
    descP.textContent = eq.description || '—';
    left.appendChild(nameHeading);
    left.appendChild(descP);
    header.appendChild(left);

    const right = document.createElement('div');
    right.className = 'flex items-center gap-2 flex-shrink-0 whitespace-nowrap';
    const editA = document.createElement('a');
    editA.href = '#';
    editA.className = 'btn btn-sm btn-ghost';
    editA.textContent = 'Edit';
    editA.addEventListener('click', function(e) { e.preventDefault(); openEditEquipment(eq.id); });
    right.appendChild(editA);

    const delForm = document.createElement('form');
    delForm.method = 'post';
    const basePath = window.location.pathname.replace(/\/$/, '');
    delForm.action = basePath + '/equipment/' + encodeURIComponent(eq.id) + '/delete/';
    delForm.className = 'inline';
    delForm.onsubmit = function() { return confirm('Delete this equipment item?'); };
    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    const existingCsrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (existingCsrf) csrf.value = existingCsrf.value;
    delForm.appendChild(csrf);
    const delBtn = document.createElement('button');
    delBtn.type = 'submit';
    delBtn.className = 'btn btn-sm btn-error';
    delBtn.textContent = 'Delete';
    delForm.appendChild(delBtn);
    right.appendChild(delForm);

    header.appendChild(right);
    label.appendChild(header);
    outer.appendChild(label);

    const content = document.createElement('div');
    content.className = 'collapse-content p-0';
    const body = document.createElement('div');
    body.className = 'card-body';
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';

    // removed Count display — no value available

    const dLoc = document.createElement('div');
    const hLoc = document.createElement('h3');
    hLoc.className = 'font-semibold';
    hLoc.textContent = 'Location';
    const pLoc = document.createElement('p');
    pLoc.className = 'text-sm';
    pLoc.textContent = (eq.location && (eq.location.name || eq.location)) || '—';
    dLoc.appendChild(hLoc);
    dLoc.appendChild(pLoc);
    grid.appendChild(dLoc);

    const dDesc = document.createElement('div');
    dDesc.className = 'md:col-span-2';
    const hDesc = document.createElement('h3');
    hDesc.className = 'font-semibold';
    hDesc.textContent = 'Description';
    const pDesc = document.createElement('p');
    pDesc.className = 'text-sm';
    pDesc.textContent = eq.description || '—';
    dDesc.appendChild(hDesc);
    dDesc.appendChild(pDesc);
    grid.appendChild(dDesc);

    const dNotes = document.createElement('div');
    dNotes.className = 'md:col-span-2';
    const hNotes = document.createElement('h3');
    hNotes.className = 'font-semibold';
    hNotes.textContent = 'Notes';
    dNotes.appendChild(hNotes);
    if (eq.notes && eq.notes.length) {
      const ul = document.createElement('ul');
      ul.className = 'list-disc list-inside text-sm';
      eq.notes.forEach(n => { const li = document.createElement('li'); li.textContent = n; ul.appendChild(li); });
      dNotes.appendChild(ul);
    } else {
      const pN = document.createElement('p'); pN.className = 'text-sm'; pN.textContent = '—'; dNotes.appendChild(pN);
    }
    grid.appendChild(dNotes);

    body.appendChild(grid);
    content.appendChild(body);
    outer.appendChild(content);

    return outer;
  }

  function upsertEquipmentCard(eq) {
    const container = document.querySelector('#collapse-equipment-toggle').closest('.collapse').querySelector('.collapse-content .p-4');
    if (!container) return;
    const existing = container.querySelector('#collapse-equipment-' + eq.id);
    if (existing) {
      const outer = existing.closest('.collapse.card');
      if (outer) {
        const newEl = buildEquipmentCard(eq);
        outer.replaceWith(newEl);
        return;
      }
    }
    const newCard = buildEquipmentCard(eq);
    container.insertBefore(newCard, container.firstChild);
  }

  // expose equipment upsert for other modules that handle equipment form submits
  window.upsertEquipmentCard = upsertEquipmentCard;

  // Ensure `form` refers to the Location quick-add form. It may not exist on every page.
  const locPanel = document.querySelector('.quick-add-panel[data-panel="location"]');
  const form = locPanel ? locPanel.querySelector('form[action][method="post"]') : null;
  if (!form) {
    // Nothing to wire up for locations on this page
  } else {
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
  }

  // Equipment quick-add AJAX submit (uses save_equipment endpoint)
  const equipPanel = document.querySelector('.quick-add-panel[data-panel="equipment"]');
  if (equipPanel) {
    const equipForm = equipPanel.querySelector('form[action][method="post"]');
    if (equipForm) {
      equipForm.addEventListener('submit', function(ev) {
        ev.preventDefault();
        clearAjaxErrors();

        // sync notes into hidden input if notes UI exists
        try {
          if (window._notesPanels && window._notesPanels['equipment'] && typeof window._notesPanels['equipment'].getNotes === 'function') {
            const notes = window._notesPanels['equipment'].getNotes() || [];
            const hiddenNotes = equipForm.querySelector('input[name="notes"]');
            if (hiddenNotes) hiddenNotes.value = JSON.stringify(notes);
          }
        } catch (e) {
          console.warn('equipment notes sync failed', e);
        }

        const base = window.location.pathname.replace(/\/?$/, '');
        const action = base + '/equipment/save/';
        const fd = new FormData(equipForm);
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
            // upsert equipment card
            if (window.upsertEquipmentCard && typeof window.upsertEquipmentCard === 'function') {
              window.upsertEquipmentCard(body.equipment);
            }
            // clear form and UI
            equipForm.reset();
            const idHidden = equipForm.querySelector('input[name="id"]');
            if (idHidden) idHidden.remove();
            const submitBtn = equipForm.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.textContent = 'Add Equipment';
            if (window._notesPanels && window._notesPanels['equipment'] && typeof window._notesPanels['equipment'].clear === 'function') {
              window._notesPanels['equipment'].clear();
            }
            const notesList = equipForm.querySelector('#equipment-notes-list');
            if (notesList) notesList.innerHTML = '';
            // ensure equipment collapse is open so user sees the new/updated item
            const eqToggle = document.getElementById('collapse-equipment-toggle');
            if (eqToggle && !eqToggle.checked) eqToggle.checked = true;
          } else if (body && body.errors) {
            renderNonFieldErrors(body.errors);
            renderFieldErrors(body.errors);
          } else {
            window.location.reload();
          }
        })
        .catch(err => {
          console.error('Equipment AJAX save failed', err);
          window.location.reload();
        });
      });
    }
  }
