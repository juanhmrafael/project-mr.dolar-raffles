// Ruta: /src/app/core/masks/input-masks.ts

import type Inputmask from 'inputmask';

// Objeto que contendrá todas nuestras definiciones de máscaras, fuertemente tipadas.
export const InputMasks: { [key: string]: Inputmask.Options } = {
    fullName: {
        mask: '*{1,100}',
        definitions: {
            '*': {
                validator: "[A-Za-z\\sáéíóúÁÉÍÓÚñÑ']",
            },
        },
        placeholder: '',
    },
    /**
     * Definición de la máscara para un ID venezolano (Cédula/RIF).
     */
    venezuelanId: {
        mask: 'A-9{7,9}',
        definitions: {
            A: {
                validator: '[VEPJvepj]',
                casing: 'upper',
            },
        },
        placeholder: 'L-NNNNNNNN',
    },

    /**
     * Definición de la máscara para un teléfono celular venezolano.
     */
    venezuelanPhone: {
        mask: '(0499) 999-9999',
        definitions: {
            '9': {
                // ✅ SOLUCIÓN: El tipo correcto para 'buffer' es string[].
                validator: (
                    ch: string,
                    buffer: string[], // <--- TIPO CORREGIDO
                    pos: number
                ): boolean => {
                    if (pos === 3) return /[12]/.test(ch);
                    if (pos === 4) {
                        // ✅ SOLUCIÓN: Usar notación de corchetes para acceder al array.
                        const areaCode = `4${buffer[3]}`; // <--- USO CORREGIDO
                        if (areaCode === '41') return /[246]/.test(ch);
                        if (areaCode === '42') return /[46]/.test(ch);
                    }
                    return /[0-9]/.test(ch);
                },
            },
        },
    },

    /**
     * Definición de la máscara para un correo electrónico.
     */
    email: {
        alias: 'email',
    },
};
