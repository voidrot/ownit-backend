document.addEventListener('DOMContentLoaded', function () {
    const passwordFields = document.querySelectorAll('input[type="password"]');

    passwordFields.forEach(field => {
        field.addEventListener('input', function () {
            const value = this.value;
            const requirementsList = this.parentElement.querySelector('.password-requirements');

            if (!requirementsList) return;

            // Requirements
            const rules = {
                'length': value.length >= 8,
                'numeric': !/^\d+$/.test(value) && value.length > 0, // Not entirely numeric
                'common': true // Client-side "common" check is hard, usually server-side. We'll just assume true or skip it visually for now? 
                // actually the user asked to replace "Your password can’t be a commonly used password." with modern wording.
                // For client side, we can mainly check length and maybe "mix of chars".
                // Let's stick to what we can verify effectively: length and "not just numbers".
            };

            // Check Length
            const lengthItem = requirementsList.querySelector('[data-rule="length"]');
            if (lengthItem) {
                updateStatus(lengthItem, rules.length);
            }

            // Check entirely numeric
            const numericItem = requirementsList.querySelector('[data-rule="numeric"]');
            if (numericItem) {
                // If it's valid (not entirely numeric or empty), it passes? 
                // Wait, "Your password can’t be entirely numeric."
                // So validity is !numeric.
                // But empty string is also not entirely numeric? Usually invalid if empty.
                const valid = value.length > 0 && !/^\d+$/.test(value);
                updateStatus(numericItem, valid);
            }

            // For other rules that rely on server validation (like "common password"), 
            // we might not be able to color them real-time easily without an API call.
            // We'll focus on the ones we can check.
        });
    });

    function updateStatus(element, isValid) {
        if (isValid) {
            element.classList.add('text-success');
            element.classList.remove('text-base-content/50', 'text-error');
            // Add checkmark icon?
        } else {
            element.classList.remove('text-success');
            element.classList.add('text-error');
            element.classList.remove('text-base-content/50');
        }
    }
});
