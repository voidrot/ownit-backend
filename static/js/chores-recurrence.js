document.addEventListener('DOMContentLoaded', function () {
  const isRecurringCheckbox = document.querySelector('[name="is_recurring"]');
  const recurrenceSelect = document.querySelector('[name="recurrence"]');
  const recurrenceBlock = document.getElementById('recurrence-block');
  const dayOfWeekEl = document.querySelector('[name="recurrence_day_of_week"]');
  const dayOfMonthEl = document.querySelector('[name="recurrence_day_of_month"]');

  // defensive access to parent divs used for show/hide
  const dayOfWeek = dayOfWeekEl ? dayOfWeekEl.closest('div') : null;
  const dayOfMonth = dayOfMonthEl ? dayOfMonthEl.closest('div') : null;
  const penalizeCheckbox = document.querySelector('[name="penalize_incomplete"]');
  const penaltyAmount = document.querySelector('[name="penalty_amount"]');
  const penaltyAmountContainer = penaltyAmount ? penaltyAmount.closest('div') : null;

  function updateRecurrenceVisibility() {
    if (!recurrenceSelect) return;
    const val = recurrenceSelect.value;
    if (val === 'W') {
      if (dayOfWeek) dayOfWeek.style.display = '';
      if (dayOfMonth) dayOfMonth.style.display = 'none';
    } else if (val === 'M') {
      if (dayOfWeek) dayOfWeek.style.display = 'none';
      if (dayOfMonth) dayOfMonth.style.display = '';
    } else {
      if (dayOfWeek) dayOfWeek.style.display = '';
      if (dayOfMonth) dayOfMonth.style.display = '';
    }
  }

  function updateRecurringBlock() {
    if (!isRecurringCheckbox) return;
    if (isRecurringCheckbox.checked) {
      if (recurrenceBlock) recurrenceBlock.style.display = '';
    } else {
      if (recurrenceBlock) recurrenceBlock.style.display = 'none';
    }
  }

  function updatePenaltyVisibility() {
    if (!penalizeCheckbox) return;
    if (penalizeCheckbox.checked) {
      if (penaltyAmountContainer) penaltyAmountContainer.style.display = '';
    } else {
      if (penaltyAmountContainer) penaltyAmountContainer.style.display = 'none';
    }
  }

  if (recurrenceSelect) recurrenceSelect.addEventListener('change', updateRecurrenceVisibility);
  if (isRecurringCheckbox) isRecurringCheckbox.addEventListener('change', updateRecurringBlock);
  if (penalizeCheckbox) penalizeCheckbox.addEventListener('change', updatePenaltyVisibility);

  // initialize
  updateRecurringBlock();
  updateRecurrenceVisibility();
  updatePenaltyVisibility();
});
