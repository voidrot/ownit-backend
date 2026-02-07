// Toggle visibility and enabled state of the minimum age input
document.addEventListener('DOMContentLoaded', function () {
  try {
    const ageCheckbox = document.querySelector('input[name="age_restricted"]');
    const minContainer = document.getElementById('chore-minimum-age-container');
    const minInput = document.querySelector('input[name="minimum_age"]');

    function update() {
      const enabled = ageCheckbox && ageCheckbox.checked;
      if (minContainer) {
        minContainer.style.display = enabled ? '' : 'none';
      }
      if (minInput) {
        minInput.disabled = !enabled;
        if (!enabled) {
          // Clear value when disabled to avoid accidental submission
          try { minInput.value = ''; } catch (e) {}
        }
      }
    }

    if (ageCheckbox) ageCheckbox.addEventListener('change', update);
    // initialize
    update();
  } catch (e) {
    // defensive: avoid breaking other scripts
    console.error('chore-age-toggle error', e);
  }
});
