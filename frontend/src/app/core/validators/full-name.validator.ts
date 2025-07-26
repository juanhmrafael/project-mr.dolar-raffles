// Ruta: /src/app/core/validators/full-name.validator.ts

import { AbstractControl, ValidationErrors } from '@angular/forms';

/**
 * Valida que el control contenga al menos un nombre y un apellido.
 * Se considera válido si hay al menos dos palabras separadas por un espacio.
 */
export function fullNameValidator(
    control: AbstractControl
): ValidationErrors | null {
    const value = control.value as string;
    if (!value) {
        return null; // No es responsabilidad de este validador chequear si es requerido.
    }

    // Quita espacios extra y divide por espacios.
    const words = value.trim().split(/\s+/).filter(Boolean);

    // Si hay menos de 2 palabras, la validación falla.
    return words.length >= 2 ? null : { invalidFullName: true };
}
