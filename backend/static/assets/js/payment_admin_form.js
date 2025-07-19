/**
 * @file payment_admin_form.js
 * @description Maneja la lógica dinámica para el formulario de Pagos en el Admin de Django.
 *              Su responsabilidad se centra en el MODO DE CREACIÓN de un pago.
 *
 * Funcionalidades:
 * 1.  Filtrar dinámicamente los Métodos de Pago según la Participación seleccionada.
 * 2.  Calcular y mostrar en tiempo real el Monto a Pagar.
 * 3.  Mostrar y ocultar los campos de detalles de la transacción ('td_*').
 */
'use strict';

window.addEventListener('load', function () {
    // Asegura que el código se ejecute solo si jQuery de Django está disponible.
    if (window.django && window.django.jQuery) {
        (function ($) {
            // El DOM está listo para ser manipulado.
            $(document).ready(function () {

                // ------------------------------------------------------------------
                //  1. SELECTORES Y CONFIGURACIÓN
                // ------------------------------------------------------------------

                const participationSelect = $('#id_participation');

                // Si el select de participación está deshabilitado, estamos en modo edición.
                // En este caso, el servidor ya ha renderizado todo correctamente,
                // por lo que no se necesita ninguna acción de JavaScript.
                if (!participationSelect.length || participationSelect.prop('disabled')) {
                    return;
                }

                const paymentMethodSelect = $('#id_payment_method_used');
                const paymentDateInput = $('#id_payment_date');
                const amountDisplayDiv = $('#amount-to-pay-display');
                const dynamicFieldsContainer = $('.dynamic-fields');

                // Mapeo que define qué campos 'td_*' son relevantes para cada método.
                const fieldsConfig = {
                    'PAGO_MOVIL': ['td_reference'],
                    'TRANSFERENCIA': ['td_reference'],
                    'ZELLE': ['td_reference', 'td_email'],
                    'BINANCE': ['td_reference', 'td_binance_pay_id']
                };

                // ------------------------------------------------------------------
                //  2. FUNCIONES DE LÓGICA DE UI (SOLO PARA MODO CREACIÓN)
                // ------------------------------------------------------------------
                
                /**
                 * Muestra/oculta los campos de detalles de transacción.
                 */
                function updateTransactionFieldsVisibility() {
                    const methodType = paymentMethodSelect.find('option:selected').data('method-type');
                    dynamicFieldsContainer.find('.form-row').hide();
                    if (methodType && fieldsConfig[methodType]) {
                        fieldsConfig[methodType].forEach(fieldName => {
                            dynamicFieldsContainer.find(`.field-${fieldName}`).show();
                        });
                    }
                }

                /**
                 * Llama a la API para calcular el monto a pagar y actualiza la UI.
                 */
                function updateCalculatedAmount() {
                    // (Tu función original es correcta y no necesita cambios)
                    const participationId = participationSelect.val();
                    const paymentMethodId = paymentMethodSelect.val();
                    const rawDate = paymentDateInput.val();
                    if (!participationId || !paymentMethodId || !rawDate) {
                        amountDisplayDiv.html('');
                        return;
                    }
                    let formattedDate = rawDate;
                    if (rawDate.includes('/')) {
                        const parts = rawDate.split('/');
                        if (parts.length === 3) {
                            formattedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
                        } else {
                            amountDisplayDiv.html('<p class="errornote">Invalid date format.</p>');
                            return;
                        }
                    }
                    const url = `/payments/api/calculate-amount/?participation_id=${participationId}&payment_method_id=${paymentMethodId}&payment_date=${formattedDate}`;
                    amountDisplayDiv.html('<p><em>Calculating amount...</em></p>');
                    fetch(url)
                        .then(response => {
                            if (!response.ok) {
                                return response.json().then(err => { throw new Error(err.error || 'Server error') });
                            }
                            return response.json();
                        })
                        .then(data => {
                            const amount = parseFloat(data.amount_to_pay).toFixed(2);
                            amountDisplayDiv.html(`<p><strong>Amount to Pay:</strong> ${amount} ${data.currency}</p>`);
                        })
                        .catch(error => {
                            console.error('Error calculating amount:', error);
                            amountDisplayDiv.html(`<p class="errornote"><strong>Error:</strong> ${error.message}</p>`);
                        });
                }
                /**
                 * Llama a la API para obtener los métodos de pago filtrados.
                 * Acepta un callback para ejecutar código después de que la llamada AJAX termine.
                 * @param {function} [callback] - Función opcional a ejecutar al finalizar.
                 */
                function updatePaymentMethods(callback) {
                    const participationId = participationSelect.val();

                    if (!participationId) {
                        paymentMethodSelect.empty().append(new Option('---------', '')).prop('disabled', true);
                        if (callback) callback(); // Ejecuta el callback incluso si no hay ID.
                        return;
                    }

                    const url = `/payments/api/methods-for-participation/${participationId}/`;
                    paymentMethodSelect.prop('disabled', true).empty().append(new Option('Loading...', ''));
                    
                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            paymentMethodSelect.empty().append(new Option('---------', ''));
                            data.forEach(method => {
                                const option = new Option(method.name, method.id);
                                $(option).data('method-type', method.method_type);
                                paymentMethodSelect.append(option);
                            });
                            paymentMethodSelect.prop('disabled', false);
                            if (callback) callback(); // Ejecuta el callback al final.
                        })
                        .catch(error => {
                            console.error('Error fetching payment methods:', error);
                            paymentMethodSelect.empty().append(new Option('Error loading methods', '')).prop('disabled', true);
                            if (callback) callback(); // Ejecuta el callback incluso en caso de error.
                        });
                }

                // ------------------------------------------------------------------
                //  3. VINCULACIÓN DE EVENTOS E INICIALIZACIÓN
                // ------------------------------------------------------------------

                participationSelect.on('change', function () {
                    // Cuando el usuario cambia la participación, actualizamos los métodos.
                    // Las otras actualizaciones se dispararán por el evento 'change' del otro select.
                    updatePaymentMethods();
                });

                paymentMethodSelect.on('change', function () {
                    updateTransactionFieldsVisibility();
                    updateCalculatedAmount();
                });
                paymentDateInput.on('change', updateCalculatedAmount);

                // --- INICIALIZACIÓN AL CARGAR LA PÁGINA ---
                // ✅ ESTA ES LA LÓGICA DE CORRECCIÓN
                // Maneja el caso de que el formulario se recargue por un error de validación.
                if (participationSelect.val()) {
                    // 1. Si el select de participación ya tiene un valor, significa que
                    //    estamos en una recarga por error.

                    // 2. Guardamos el valor que tenía el método de pago (si lo tenía).
                    const previouslySelectedMethod = paymentMethodSelect.val();

                    // 3. Llamamos a updatePaymentMethods, pero le pasamos una función
                    //    (callback) que se ejecutará solo DESPUÉS de que la lista
                    //    de métodos se haya repoblado.
                    updatePaymentMethods(function () {
                        // 4. Una vez que las opciones están cargadas, restauramos la selección anterior.
                        paymentMethodSelect.val(previouslySelectedMethod);

                        // 5. Forzamos la actualización del resto de la interfaz.
                        updateTransactionFieldsVisibility();
                        updateCalculatedAmount();
                    });
                } else {
                    // Si es una carga limpia, simplemente ocultamos los campos y deshabilitamos.
                    updateTransactionFieldsVisibility();
                    paymentMethodSelect.prop('disabled', true);
                }
            });
        })(window.django.jQuery);
    }
});