document.addEventListener('DOMContentLoaded', function () {
  try {
    // handle task steps UI
    const panel = document.querySelector('.quick-add-panel[data-panel="task"]');
    if (!panel) return;

    const nameInput = panel.querySelector('#task-step-name');
    const descInput = panel.querySelector('#task-step-desc');
    const addBtn = panel.querySelector('#add-task-step');
    const listEl = panel.querySelector('#task-steps-list');
    let hidden = panel.querySelector('input[name="steps"]');

    if (!hidden) {
      const form = panel.querySelector('form');
      if (form) {
        hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'steps';
        form.appendChild(hidden);
      }
    }

    if (!nameInput || !addBtn || !listEl || !hidden) return;

    let steps = [];

    function render() {
      listEl.innerHTML = '';
      steps.forEach((s, idx) => {
        const li = document.createElement('li');
        li.className = 'flex items-center justify-between gap-2 py-1';

        const left = document.createElement('div');
        left.className = 'grow';
        const title = document.createElement('div');
        // Use `font-semibold` so other parts of the code (save handler) can reliably
        // find the step title using the same class.
        title.className = 'font-semibold';
        title.textContent = s.name;
        const desc = document.createElement('div');
        desc.className = 'text-sm text-muted';
        desc.textContent = s.description || '';
        left.appendChild(title);
        left.appendChild(desc);

        const controls = document.createElement('div');
        controls.className = 'flex items-center gap-1';

        // Only render ordering controls for non-persisted (new) steps. When
        // editing an existing task we don't want to show arrows for persisted
        // steps to avoid accidental reordering of persisted data.
        let up = null, down = null;
        if (!s.persisted) {
          up = document.createElement('button');
          up.type = 'button';
          up.className = 'btn btn-ghost btn-xs';
          up.textContent = '↑';
          up.disabled = idx === 0;
          up.addEventListener('click', function () { move(idx, idx - 1); });

          down = document.createElement('button');
          down.type = 'button';
          down.className = 'btn btn-ghost btn-xs';
          down.textContent = '↓';
          down.disabled = idx === steps.length - 1;
          down.addEventListener('click', function () { move(idx, idx + 1); });
        }

        const del = document.createElement('button');
        del.type = 'button';
        del.className = 'btn btn-error btn-xs';
        del.textContent = 'Remove';
        // Persisted steps (preloaded from an existing task) should not show a
        // remove button by default to avoid accidental deletion when editing.
        // Steps passed with a truthy `persisted` flag will hide the delete control.
        if (!s.persisted) {
          del.addEventListener('click', function () { remove(idx); });
          controls.appendChild(del);
        }

        if (up) controls.appendChild(up);
        if (down) controls.appendChild(down);

        li.appendChild(left);
        li.appendChild(controls);
        listEl.appendChild(li);
      });
      updateHidden();
    }

    function updateHidden() {
      // ensure order indexes
      const out = steps.map((s, i) => ({name: s.name, description: s.description || '', order: i}));
      hidden.value = JSON.stringify(out);
    }

    function addStep(name, desc) {
      steps.push({name: String(name).trim(), description: String(desc || ''), persisted: false});
      render();
    }

    function remove(i) {
      steps.splice(i, 1);
      render();
    }

    function move(from, to) {
      if (to < 0 || to >= steps.length) return;
      const item = steps.splice(from, 1)[0];
      steps.splice(to, 0, item);
      render();
    }

    addBtn.addEventListener('click', function (e) {
      e.preventDefault();
      const n = (nameInput.value || '').trim();
      if (!n) return;
      addStep(n, (descInput.value || '').trim());
      nameInput.value = '';
      descInput.value = '';
      nameInput.focus();
    });

    // initialize from existing hidden value
    if (hidden.value) {
      try {
        const parsed = JSON.parse(hidden.value);
        if (Array.isArray(parsed)) {
          // Map incoming structure into internal step objects. Preserve an
          // optional `persisted` flag if present so we can render controls
          // appropriately when editing an existing task.
          steps = parsed.map((p, idx) => ({
            name: p.name || '',
            description: p.description || '',
            order: (p.order != null ? p.order : idx),
            persisted: !!p.persisted || false,
          }));
          // sort by order, fallback to index
          steps.sort((a,b) => (a.order - b.order));
        }
      } catch (err) {
        // ignore
      }
    }
    render();
    // expose a small API so other scripts (open-edit) can populate steps
    window._taskStepsUI = {
      setSteps: function(arr, opts) {
        try {
          if (!Array.isArray(arr)) return;
          steps = arr.map((p, idx) => ({
            name: p.name || '',
            description: p.description || '',
            order: (p.order != null ? p.order : idx),
            persisted: !!(opts && opts.persisted) || !!p.persisted || false,
          }));
          steps.sort((a,b) => (a.order - b.order));
          render();
        } catch (e) { console.warn('setSteps failed', e); }
      },
      getSteps: function() {
        return steps.map((s, i) => ({ name: s.name, description: s.description || '', order: i }));
      }
    };
  } catch (err) {
    console.error('Steps UI error', err);
  }
});
