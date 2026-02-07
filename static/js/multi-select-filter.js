document.addEventListener('DOMContentLoaded', function () {
  function setupFilter(filterId, optionsId) {
    var filter = document.getElementById(filterId);
    var options = document.getElementById(optionsId);
    if (!filter || !options) return;
    filter.addEventListener('input', function (e) {
      var q = e.target.value.trim().toLowerCase();
      var labels = options.querySelectorAll('label');
      labels.forEach(function (lbl) {
        var text = lbl.textContent.trim().toLowerCase();
        if (!q || text.indexOf(q) !== -1) {
          lbl.style.display = '';
        } else {
          lbl.style.display = 'none';
        }
      });
    });
    // Wire up clear button if present
    var clearBtn = document.getElementById(filterId.replace('-filter', '-clear'));
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        filter.value = '';
        filter.dispatchEvent(new Event('input'));
        filter.focus();
      });
    }
  }

  setupFilter('chore-equipment-filter', 'chore-equipment-options');
  setupFilter('chore-tasks-filter', 'chore-tasks-options');
  setupFilter('task-equipment-filter', 'task-equipment-options');
});
