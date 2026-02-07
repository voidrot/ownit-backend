document.addEventListener('DOMContentLoaded', function () {
  const tabs = Array.from(document.querySelectorAll('[role="tab"][data-tab]'));
  const panels = Array.from(document.querySelectorAll('.quick-add-panel'));
  if (!tabs.length || !panels.length) return;

  // Activate by tab element
  function activate(tab) {
    const target = tab.getAttribute('data-tab');
    activateByName(target);
  }

  // Activate by panel name (shared helper)
  function activateByName(target) {
    tabs.forEach(t => {
      const selected = t.getAttribute('data-tab') === target;
      t.classList.toggle('tab-active', selected);
      t.setAttribute('aria-selected', String(selected));
    });
    panels.forEach(p => {
      if (p.getAttribute('data-panel') === target) p.classList.remove('hidden');
      else p.classList.add('hidden');
    });
  }

  // expose a global helper so other scripts can activate tabs without duplicating logic
  window.activateQuickAddTab = activateByName;

  tabs.forEach(t => t.addEventListener('click', () => activate(t)));

  // keyboard navigation for tabs
  tabs.forEach((t, i) => {
    t.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        const dir = e.key === 'ArrowRight' ? 1 : -1;
        const next = (i + dir + tabs.length) % tabs.length;
        tabs[next].focus();
        activate(tabs[next]);
        e.preventDefault();
      }
    });
  });
});
