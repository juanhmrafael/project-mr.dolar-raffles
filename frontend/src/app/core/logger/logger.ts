// src/app/core/logger/logger.ts
import { Injectable, isDevMode } from '@angular/core';

@Injectable({
    providedIn: 'root',
})
export class LoggerService {
    private readonly isDevelopment = isDevMode();

    log(message: any, ...optionalParams: any[]): void {
        if (this.isDevelopment) {
            console.log(message, ...optionalParams);
        }
    }

    warn(message: any, ...optionalParams: any[]): void {
        if (this.isDevelopment) {
            console.warn(message, ...optionalParams);
        }
    }

    error(message: any, ...optionalParams: any[]): void {
        // Los errores críticos se pueden loguear siempre, o enviar a un servicio de tracking
        // Para este caso, los mostraremos siempre.
        console.error(message, ...optionalParams);
    }
}
