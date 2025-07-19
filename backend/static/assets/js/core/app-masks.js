// static/assets/js/core/app-masks.js

// Creamos un namespace global para nuestra aplicación para evitar contaminar 'window'.
// Si AppCore no existe, lo creamos. Si ya existe, lo usamos.
var AppCore = window.AppCore || {};

(function (AppCore) {
    'use strict';

    // Objeto que contendrá todas nuestras definiciones de máscaras.
    AppCore.Masks = {


        /**
         * Definición de la máscara para un ID venezolano (Cédula/RIF).
         * @returns {object} - Objeto de configuración para Inputmask.
         */
        getVenezuelanIdMask: function () {
            return {
                mask: "A-9{7,9}",
                definitions: {
                    'A': {
                        validator: "[VEPJGCvepjgc]",
                        casing: "upper"
                    }
                },
                placeholder: "L-NNNNNNNN"
            };
        },

        /**
         * Definición de la máscara para un teléfono celular venezolano.
         * Valida los códigos de operadora en tiempo real.
         * @returns {object} - Objeto de configuración para Inputmask.
         */
        getVenezuelanPhoneMask: function () {
            // Esta es la lógica de validación pura, sin cambios.
            const validatorLogic = function (ch, buffer, pos, strict, opts) {
                if (pos === 3) return /[12]/.test(ch);
                if (pos === 4) {
                    const areaCode = `4${buffer.buffer[3]}`;
                    if (areaCode === '41') return /[246]/.test(ch);
                    if (areaCode === '42') return /[46]/.test(ch);
                }
                return new RegExp("[0-9]").test(ch);
            };

            return {
                mask: "(0499) 999-9999",
                definitions: {
                    '9': {
                        validator: validatorLogic
                    }
                }
            };
        },

        /**
         * Definición de la máscara para un nombre de persona.
         * Permite letras, acentos, ñ, y espacios. No permite números ni la mayoría de símbolos.
         * @returns {object} - Objeto de configuración para Inputmask.
         */
        getFullNameMask: function () {
            return {
                // Usamos una expresión regular para definir los caracteres permitidos.
                // El '+' significa 'uno o más' de los caracteres del conjunto.
                mask: "*{1,100}", // Permite hasta 100 caracteres.
                definitions: {
                    '*': {
                        // Letras mayúsculas y minúsculas, acentos comunes, ñ, y espacio.
                        validator: "[A-Za-z\\sáéíóúÁÉÍÓÚñÑ']"
                    }
                },
                placeholder: ""
            };
        },

        /**
         * Definición de la máscara para un correo electrónico.
         * Aprovecha el alias 'email' incorporado en Inputmask, que es muy robusto.
         * @returns {object} - Objeto de configuración para Inputmask.
         */
        getEmailMask: function () {
            return {
                // 'email' es un alias predefinido y altamente probado por la comunidad.
                alias: 'email',
            };
        },

        /**
         * Definición de la máscara para un número de cuenta bancaria venezolana.
         * Formato: 20 dígitos numéricos.
         * @returns {object} - Objeto de configuración para Inputmask.
         */
        getBankAccountMask: function () {
            return {
                // '9' representa un dígito numérico.
                mask: "99999999999999999999", // 20 dígitos
                placeholder: ""
            };
        }


    };
    // Adjuntamos el objeto AppCore modificado de vuelta al scope global.
    window.AppCore = AppCore;

})(window.AppCore);