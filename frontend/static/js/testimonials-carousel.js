// ============================================
// Carrusel de testimonios (3 visibles, gira ambos lados)
// Requiere el markup de _carrusel_testimonios.html
// ============================================
(function () {
    function init() {
        var carrusel = document.getElementById('testiCarousel');
        if (!carrusel) return;

        var track = carrusel.querySelector('.testi-track');
        var slides = track.querySelectorAll('.testi-slide');
        var dotsWrap = carrusel.querySelector('.testi-dots');
        var actual = 0;

        function porVista() {
            var ancho = window.innerWidth;
            if (ancho <= 640) return 1;
            if (ancho <= 1024) return 2;
            return 3;
        }

        function maxIndex() {
            return Math.max(0, slides.length - porVista());
        }

        function crearDots() {
            dotsWrap.innerHTML = '';
            for (var i = 0; i <= maxIndex(); i++) {
                var d = document.createElement('button');
                d.className = 'testi-dot' + (i === actual ? ' active' : '');
                d.setAttribute('aria-label', 'Grupo ' + (i + 1));
                (function (idx) {
                    d.addEventListener('click', function () { irA(idx); });
                })(i);
                dotsWrap.appendChild(d);
            }
        }

        function refrescar() {
            var paso = 100 / porVista();
            track.style.transform = 'translateX(-' + (actual * paso) + '%)';
            carrusel.querySelectorAll('.testi-dot').forEach(function (d, i) {
                d.classList.toggle('active', i === actual);
            });
        }

        function irA(indice) {
            actual = Math.min(Math.max(indice, 0), maxIndex());
            refrescar();
        }

        carrusel.querySelector('.testi-next').addEventListener('click', function () {
            irA(actual >= maxIndex() ? 0 : actual + 1);
        });
        carrusel.querySelector('.testi-prev').addEventListener('click', function () {
            irA(actual <= 0 ? maxIndex() : actual - 1);
        });

        // Deslizar en movil
        var toqueX = null;
        carrusel.addEventListener('touchstart', function (e) {
            toqueX = e.touches[0].clientX;
        }, { passive: true });
        carrusel.addEventListener('touchend', function (e) {
            if (toqueX === null) return;
            var delta = e.changedTouches[0].clientX - toqueX;
            if (Math.abs(delta) > 40) {
                delta < 0
                    ? carrusel.querySelector('.testi-next').click()
                    : carrusel.querySelector('.testi-prev').click();
            }
            toqueX = null;
        }, { passive: true });

        window.addEventListener('resize', function () {
            irA(Math.min(actual, maxIndex()));
            crearDots();
            refrescar();
        });

        crearDots();
        refrescar();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
