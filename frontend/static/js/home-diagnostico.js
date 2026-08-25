// ============================================
// Mini diagnostico del home (form de 5 pasos)
// ============================================
(function () {
    var currentStep = 1;
    const totalSteps = 5;

    function nextStep() {
        if (currentStep < totalSteps) {
            const current = document.querySelector('.step[data-step="' + currentStep + '"]');
            const select = current.querySelector('select');
            if (select && select.required && !select.value) {
                select.reportValidity();
                return;
            }
            current.classList.remove('active');
            currentStep++;
            document.querySelector('.step[data-step="' + currentStep + '"]').classList.add('active');
            updateProgress();
        }
    }

    function prevStep() {
        if (currentStep > 1) {
            document.querySelector('.step[data-step="' + currentStep + '"]').classList.remove('active');
            currentStep--;
            document.querySelector('.step[data-step="' + currentStep + '"]').classList.add('active');
            updateProgress();
        }
    }

    function updateProgress() {
        document.querySelectorAll('.diagnostic-progress .dot').forEach((dot, index) => {
            dot.classList.toggle('active', index < currentStep);
            dot.classList.toggle('completed', index < currentStep - 1);
        });
    }

    // Enviar nombre de condominium desde el campo final antes del submit
    function init() {
        updateProgress();

        // Botones siguiente/anterior sin onclick inline (CSP estricta)
        document.querySelectorAll('[data-accion="siguiente"]').forEach(function (btn) {
            btn.addEventListener('click', nextStep);
        });
        document.querySelectorAll('[data-accion="anterior"]').forEach(function (btn) {
            btn.addEventListener('click', prevStep);
        });

        const form = document.querySelector('.diagnostic-form form');
        if (form) {
            form.addEventListener('submit', () => {
                const finalField = form.querySelector('[name="condominium_name_final"]');
                const hiddenField = form.querySelector('[name="condominium_name"]');
                if (finalField && hiddenField) {
                    hiddenField.value = finalField.value;
                }
            });
        }

        // Auto-dismiss flash messages
        setTimeout(() => {
            document.querySelectorAll('.flash-message').forEach(el => el.remove());
        }, 6000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
