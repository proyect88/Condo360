// ============================================
// Carrusel del cintillo en detalle de servicio
// ============================================
(function () {
    function init() {
        var carousel = document.getElementById('serviceCarousel');
        if (!carousel) return;

        var slides = carousel.querySelectorAll('.carousel-slide');
        if (slides.length < 2) return;

        var dotsWrap = carousel.querySelector('.carousel-dots');
        var actual = 0;
        var timer = null;
        var intervalo = parseInt(carousel.getAttribute('data-autoplay'), 10) || 5000;

        slides.forEach(function (_, i) {
            var dot = document.createElement('button');
            dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
            dot.setAttribute('aria-label', 'Imagen ' + (i + 1));
            dot.addEventListener('click', function () { irA(i); });
            dotsWrap.appendChild(dot);
        });
        var dots = dotsWrap.querySelectorAll('.carousel-dot');

        function irA(indice) {
            slides[actual].classList.remove('active');
            dots[actual].classList.remove('active');
            actual = (indice + slides.length) % slides.length;
            slides[actual].classList.add('active');
            dots[actual].classList.add('active');
        }

        function siguiente() { irA(actual + 1); }
        function anterior() { irA(actual - 1); }

        function iniciar() {
            detener();
            timer = setInterval(siguiente, intervalo);
        }
        function detener() {
            if (timer) { clearInterval(timer); timer = null; }
        }

        carousel.querySelector('.carousel-next').addEventListener('click', function () { siguiente(); iniciar(); });
        carousel.querySelector('.carousel-prev').addEventListener('click', function () { anterior(); iniciar(); });

        carousel.addEventListener('mouseenter', detener);
        carousel.addEventListener('mouseleave', iniciar);

        // Deslizar en movil
        var toqueX = null;
        carousel.addEventListener('touchstart', function (e) { toqueX = e.touches[0].clientX; }, { passive: true });
        carousel.addEventListener('touchend', function (e) {
            if (toqueX === null) return;
            var delta = e.changedTouches[0].clientX - toqueX;
            if (Math.abs(delta) > 40) { delta < 0 ? siguiente() : anterior(); }
            toqueX = null;
            iniciar();
        }, { passive: true });

        iniciar();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
