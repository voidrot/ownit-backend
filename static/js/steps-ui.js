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
        title.className = 'font-medium';
        title.textContent = s.name;
        const desc = document.createElement('div');
        desc.className = 'text-sm text-muted';
        desc.textContent = s.description || '';
        left.appendChild(title);
        left.appendChild(desc);

        const controls = document.createElement('div');
        controls.className = 'flex items-center gap-1';

        const up = document.createElement('button');
        up.type = 'button';
        up.className = 'btn btn-ghost btn-xs';
        up.textContent = '↑';
        up.disabled = idx === 0;
        up.addEventListener('click', function () { move(idx, idx - 1); });

        const down = document.createElement('button');
        down.type = 'button';
        down.className = 'btn btn-ghost btn-xs';
        down.textContent = '↓';
        down.disabled = idx === steps.length - 1;
        down.addEventListener('click', function () { move(idx, idx + 1); });

        const del = document.createElement('button');
        del.type = 'button';
        del.className = 'btn btn-error btn-xs';
        del.textContent = 'Remove';
        del.addEventListener('click', function () { remove(idx); });

        controls.appendChild(up);
        controls.appendChild(down);
        controls.appendChild(del);

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
      steps.push({name: String(name).trim(), description: String(desc || '')});
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
          steps = parsed.map(p => ({name: p.name || '', description: p.description || '', order: (p.order != null ? p.order : 0)}));
          // sort by order, fallback to index
          steps.sort((a,b) => (a.order - b.order));
        }
      } catch (err) {
        // ignore
      }
    }
    render();
  } catch (err) {
    console.error('Steps UI error', err);
  }
});
