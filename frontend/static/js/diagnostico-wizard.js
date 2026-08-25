// ============================================
// Wizard del diagnostico integral (/diagnostico)
// ============================================
(function () {
    function init() {
        var form = document.getElementById('diagForm');
        if (!form) return;

        var pasos = Array.prototype.slice.call(form.querySelectorAll('.step'));
        var actual = 0;
        var titulos = ['Tu condominio', 'Problemas detectados', 'Urgencia y presupuesto',
                       'Contacto preferido', 'Tus datos'];
        var barra = document.getElementById('diagBarra');
        var pasoNum = document.getElementById('diagPasoActual');
        var pasoTitulo = document.getElementById('diagPasoTitulo');

        function mostrar(indice, desplazar) {
            pasos.forEach(function (fs, i) { fs.classList.toggle('active', i === indice); });
            actual = indice;
            if (barra) barra.style.width = ((indice + 1) / pasos.length * 100) + '%';
            if (pasoTitulo) pasoTitulo.textContent = titulos[indice];
            var paso = pasos[indice];
            if (pasoNum) pasoNum.textContent = indice + 1;
            // Desplazar y animar SOLO cuando se cambia de paso a proposito.
            // En la carga inicial desplazar es undefined -> NO se mueve.
            if (desplazar) {
                paso.classList.remove('animar');
                void paso.offsetWidth; /* reinicia la animacion */
                paso.classList.add('animar');
                form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }

        function validarPaso(fs) {
            var ok = true;

            // Campos requeridos estandar
            fs.querySelectorAll('input[required], select[required]').forEach(function (campo) {
                if (!campo.checkValidity()) {
                    campo.reportValidity();
                    ok = false;
                }
            });
            if (!ok) return false;

            // Al menos un problema marcado (paso 2)
            var checks = fs.querySelectorAll('input[name="issue_types"]');
            if (checks.length) {
                var alguno = Array.prototype.some.call(checks, function (c) { return c.checked; });
                var aviso = fs.querySelector('[data-error-for="issue_types"]');
                if (aviso) aviso.hidden = alguno;
                if (!alguno) {
                    checks[0].focus();
                    return false;
                }
            }
            return true;
        }

        form.querySelectorAll('[data-siguiente]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (validarPaso(pasos[actual])) mostrar(actual + 1, true);
            });
        });

        form.querySelectorAll('[data-anterior]').forEach(function (btn) {
            btn.addEventListener('click', function () { mostrar(actual - 1, true); });
        });

        // Resaltar tarjetas de seleccion
        form.querySelectorAll('.issue-option input').forEach(function (chk) {
            chk.addEventListener('change', function () {
                chk.closest('.issue-option').classList.toggle('elegida', chk.checked);
                var avisos = form.querySelector('[data-error-for="issue_types"]');
                if (avisos && chk.checked) avisos.hidden = true;
            });
        });

        // Validacion final antes de enviar
        form.addEventListener('submit', function (e) {
            if (!form.checkValidity() || !validarPaso(pasos[actual])) {
                e.preventDefault();
                form.reportValidity();
            }
        });

        mostrar(0);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
