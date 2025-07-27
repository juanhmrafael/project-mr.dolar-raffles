window.addEventListener('load', function () {
    if (window.django && window.django.jQuery) {
        (function ($) {
            $(document).ready(function () {

                // --- SELECTORES ---
                const idElement = document.getElementById('id_identification_number');
                const nameElement = document.getElementById('id_full_name');
                const emailElement = document.getElementById('id_email');
                
                if (typeof Inputmask !== 'undefined' && typeof AppCore !== 'undefined') {
                    // --- APLICACIÓN DE MÁSCARAS (Ahora es solo una llamada a la lógica pura) ---
                    // Cédula/RIF
                    if (idElement) {
                        const idMaskConfig = AppCore.Masks.getVenezuelanIdMask();
                        new Inputmask(idMaskConfig).mask(idElement);
                    }

                    // Nombre del participante
                    if (nameElement) {
                        const nameMaskConfig = AppCore.Masks.getFullNameMask();
                        new Inputmask(nameMaskConfig).mask(nameElement);
                    }

                    // Correo Electrónico
                    if (emailElement) {
                        const emailMaskConfig = AppCore.Masks.getEmailMask();
                        new Inputmask(emailMaskConfig).mask(emailElement);
                    }

                }

            });
        })(window.django.jQuery);
    }
});