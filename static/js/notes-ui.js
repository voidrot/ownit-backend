document.addEventListener('DOMContentLoaded', function () {
  try {
    // Support multiple quick-add panels that need a notes UX (e.g., location, equipment)
    // Panels should include elements with IDs like `<panel>-note-text`, `add-<panel>-note`, and `<panel>-notes-list`.
    const panels = Array.from(document.querySelectorAll('.quick-add-panel[data-panel]'))
      .map(el => el.getAttribute('data-panel'))
      .filter(Boolean);

    panels.forEach(function (panelName) {
      const panel = document.querySelector('.quick-add-panel[data-panel="' + panelName + '"]');
      if (!panel) return;

      const noteText = panel.querySelector('#' + panelName + '-note-text');
      const addBtn = panel.querySelector('#add-' + panelName + '-note');
      const notesList = panel.querySelector('#' + panelName + '-notes-list');
      let hiddenNotes = panel.querySelector('input[name="notes"]');

      // If the form widget didn't render a hidden notes input for some reason, create one
      if (!hiddenNotes) {
        const form = panel.querySelector('form');
        if (form) {
          hiddenNotes = document.createElement('input');
          hiddenNotes.type = 'hidden';
          hiddenNotes.name = 'notes';
          form.appendChild(hiddenNotes);
        }
      }

      // Normalize server-side 'null' string to empty
      if (hiddenNotes && typeof hiddenNotes.value === 'string' && hiddenNotes.value.trim().toLowerCase() === 'null') {
        hiddenNotes.value = '';
      }

      if (!noteText || !addBtn || !notesList) return;

      let notes = [];

      function renderNotes() {
        notesList.innerHTML = '';
        notes.forEach((n, idx) => {
          const li = document.createElement('li');
          li.className = 'flex items-center justify-between';
          const span = document.createElement('span');
          span.textContent = n;
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'btn btn-ghost btn-xs ml-2';
          btn.textContent = 'Remove';
          btn.addEventListener('click', function () {
            notes.splice(idx, 1);
            updateHidden();
            renderNotes();
          });
          li.appendChild(span);
          li.appendChild(btn);
          notesList.appendChild(li);
        });
      }

      function updateHidden() {
        if (hiddenNotes) hiddenNotes.value = JSON.stringify(notes);
      }

      addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const v = (noteText.value || '').trim();
        if (!v) return;
        notes.push(v);
        noteText.value = '';
        updateHidden();
        renderNotes();
        noteText.focus();
      });

      // initialize from any prefilled hidden value
      if (hiddenNotes && hiddenNotes.value) {
        try {
          const parsed = JSON.parse(hiddenNotes.value);
          if (Array.isArray(parsed)) notes = parsed.map(String).filter(s => s.trim());
        } catch (err) {
          // ignore parse errors
        }
      }
      renderNotes();
    });
  } catch (err) {
    console.error('Notes UI error', err);
  }
});
