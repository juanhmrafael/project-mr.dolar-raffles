import {
    ApplicationConfig,
    provideZoneChangeDetection,
    importProvidersFrom,
    LOCALE_ID,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { routes } from './app.routes';

import {
    LucideAngularModule,
    Trophy,
    Ticket,
    Award,
    Search,
    Bell,
    Clock,
    History,
    ArrowRight,
    Zap,
    Loader,
    Sparkles,
    HandCoins,
    MapPin,
    Navigation,
    Info,
    Phone,
    Banknote,
    Shield,
    Utensils,
    Heart,
    Star,
    Check,
    Copyright,
    Users,
    Link,
    ChevronRight,
    Mail,
    X,
    CheckCircle,
    CheckCircle2,
} from 'lucide-angular';

// ✅ 1. IMPORTA LOS DATOS DE LOCALIZACIÓN
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { provideHttpClient, withFetch } from '@angular/common/http';

// ✅ 2. REGISTRA LA LOCALIZACIÓN
registerLocaleData(localeEs, 'es');

export const appConfig: ApplicationConfig = {
    providers: [
        provideZoneChangeDetection({ eventCoalescing: true }),
        provideRouter(routes, withComponentInputBinding()),
        provideHttpClient(withFetch()),
        importProvidersFrom(
            LucideAngularModule.pick({
                Trophy,
                Ticket,
                Award,
                Search,
                Bell,
                Clock,
                History,
                ArrowRight,
                Zap,
                Loader,
                Sparkles,
                HandCoins,
                MapPin,
                Navigation,
                Info,
                Phone,
                Banknote,
                Shield,
                Utensils,
                Heart,
                Star,
                Check,
                Copyright,
                Users,
                Link,
                ChevronRight,
                Mail,
                X,
                CheckCircle,
                CheckCircle2,
            })
        ),
        { provide: LOCALE_ID, useValue: 'es' },
    ],
};
