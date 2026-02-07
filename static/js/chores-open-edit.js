// Open edit fallback for chores page
function openEditChore(id) {
  // navigate to same path with ?edit=<id>
  window.location.href = window.location.pathname + '?edit=' + id;
}

// expose globally for inline handlers to call
window.openEditChore = openEditChore;
