window.addEventListener('load', function () {
    if (window.django && window.django.jQuery) {
        (function ($) {
            $(document).ready(function () {

                const currencyMap = {
                    'PAGO_MOVIL': 'VEF',
                    'TRANSFERENCIA': 'VEF',
                    'ZELLE': 'USD',
                    'BINANCE': 'USD',
                    '': '---' // Valor por defecto si no se selecciona nada
                };

                // --- SELECTORES ---
                const phoneElement = document.getElementById('id_custom_phone');
                const idElement = document.getElementById('id_custom_id_number');
                const nameElement = document.getElementById('id_custom_holder_name');
                const emailElement = document.getElementById('id_custom_email');
                const accountElement = document.getElementById('id_custom_account_number');
                const currencyDisplayInput = $('#id_currency_display');
                const methodTypeSelector = $('#id_method_type');


                if (typeof Inputmask !== 'undefined' && typeof AppCore !== 'undefined') {
                    // --- APLICACIÓN DE MÁSCARAS (Ahora es solo una llamada a la lógica pura) ---
                    // Teléfono
                    if (phoneElement) {
                        // Obtenemos la configuración de la máscara desde nuestro núcleo reutilizable.
                        const phoneMaskConfig = AppCore.Masks.getVenezuelanPhoneMask();
                        new Inputmask(phoneMaskConfig).mask(phoneElement);
                    }

                    // Cédula/RIF
                    if (idElement) {
                        const idMaskConfig = AppCore.Masks.getVenezuelanIdMask();
                        new Inputmask(idMaskConfig).mask(idElement);
                    }

                    // Nombre del Titular
                    if (nameElement) {
                        const nameMaskConfig = AppCore.Masks.getFullNameMask();
                        new Inputmask(nameMaskConfig).mask(nameElement);
                    }

                    // Correo Electrónico
                    if (emailElement) {
                        const emailMaskConfig = AppCore.Masks.getEmailMask();
                        new Inputmask(emailMaskConfig).mask(emailElement);
                    }

                    // Número de Cuenta
                    if (accountElement) {
                        const accountMaskConfig = AppCore.Masks.getBankAccountMask();
                        new Inputmask(accountMaskConfig).mask(accountElement);
                    }
                }

                const fieldsConfig = {
                    'PAGO_MOVIL': ['custom_phone', 'custom_id_number', 'custom_bank'],
                    'TRANSFERENCIA': ['custom_account_number', 'custom_holder_name', 'custom_id_number', 'custom_bank'],
                    'ZELLE': ['custom_email', 'custom_holder_name'],
                    'BINANCE': ['custom_pay_id', 'custom_holder_name']
                };

                /**
                 * Obtiene la fila del formulario que contiene el campo especificado.
                 * @param {string} fieldName - Nombre del campo a buscar
                 * @returns {jQuery|null} - Elemento jQuery de la fila o null si no se encuentra
                 */
                function getFieldRow(fieldName) {
                    const fieldId = `#id_${fieldName}`;
                    const fieldElement = $(fieldId);

                    if (fieldElement.length === 0) {
                        // console.warn(`[Depuración] No se encontró el elemento del campo con ID: ${fieldId}`);
                        return null;
                    }

                    const formRow = fieldElement.closest('.form-row');
                    if (formRow.length === 0) {
                        // console.warn(`[Depuración] Se encontró el campo ${fieldId}, pero no su contenedor .form-row.`);
                        return null;
                    }

                    return formRow;
                }

                /**
                 * Actualiza la visibilidad de los campos del formulario
                 * basándose en el tipo de método de pago seleccionado.
                 */
                function updateFormVisibility() {
                    const selectedMethod = $('#id_method_type').val();

                    // Ocultar todos los campos dinámicos primero
                    Object.values(fieldsConfig).flat().forEach(fieldName => {
                        const row = getFieldRow(fieldName);
                        if (row) {
                            row.hide();
                        }
                    });

                    // Mostrar solo los campos para el método seleccionado
                    if (selectedMethod && fieldsConfig[selectedMethod]) {
                        fieldsConfig[selectedMethod].forEach(fieldName => {
                            const row = getFieldRow(fieldName);
                            if (row) {
                                row.show();
                            }
                        });
                    }

                    // Actualizamos el valor de nuestro campo de visualización.
                    if (currencyDisplayInput.length > 0) {
                        const newCurrency = currencyMap[selectedMethod] || '---';
                        currencyDisplayInput.val(newCurrency);
                    }
                }

                // Inicialización y eventos
                if (methodTypeSelector.length > 0) {
                    // Vincular el evento change
                    methodTypeSelector.on('change', updateFormVisibility);

                    // Establecer estado inicial
                    updateFormVisibility();
                }
            });
        })(window.django.jQuery);
    }
});