import { isPlatformBrowser } from '@angular/common';
import {
    DOCUMENT,
    effect,
    inject,
    Injectable,
    PLATFORM_ID,
    signal,
} from '@angular/core';
import {
    ContactInfo,
    FooterLink,
    NavLink,
    SocialLink,
    Theme,
} from '../../shared/models/layout.types';
import { User } from '../../shared/models/user.types';

@Injectable({
    providedIn: 'root',
})
export class LayoutStore {
    private readonly document = inject(DOCUMENT);
    private readonly platformId = inject(PLATFORM_ID);

    public readonly companyName = signal<string>('Gana con Sandra');
    public readonly footerTagline = signal<string>(
        '¡La mejor comida al mejor precio!'
    );
    public readonly footerDescription = signal<string>(
        'Descubre el sabor auténtico con Mr. Dólar. Ofrecemos comida deliciosa y de calidad a precios increíbles. ¡Ven y disfruta de una experiencia gastronómica única!'
    );
    public readonly appLogoUrl = signal<string>('/assets/logo.svg');
    public readonly theme = signal<Theme>('light');

    public readonly footerLinks = signal<FooterLink[]>([
        {
            path: '#',
            label: 'Términos y Condiciones',
            action: 'openTermsModal',
        },
    ]);

    public readonly mainNavLinks = signal<NavLink[]>([
        { label: 'Inicio', path: '/' },
        { label: 'Ubícanos', path: '/location/' },
    ]);

    public readonly footerQuickLinks = signal<FooterLink[]>([
        { path: '/', label: 'Inicio' },
        { label: 'Ubícanos', path: '/location/' },
    ]);

    public readonly footerSocialLinks = signal<SocialLink[]>([
        // { platform: 'facebook', url: '#' },
        {
            platform: 'instagram',
            url: 'https://www.instagram.com/misterdolar1?igsh=b3BwOGN0czc5dW16',
        },
        // { platform: 'twitter', url: '#' },
        { platform: 'whatsapp', url: 'https://wa.me/584244199668' },
        {
            platform: 'tiktok',
            url: 'https://www.tiktok.com/@misterdolar1valencia?_t=ZM-8yBeKDIXFLy&_r=1',
        },
    ]);

    public readonly footerContactInfo = signal<ContactInfo>({
        phone: '(0424) 419-9668',
        address:
            'Entre Manrique y Cantaura, Calle Boyaca, Casa 94 21 Toldo Amarillo, Valencia 2001, Carabobo',
        hours: [
            'Lunes - Viernes: 8:00 AM - 8:00 PM',
            'Sábados: 9:00 AM - 9:00 PM',
            'Domingos: 10:00 AM - 6:00 PM',
        ],
    });

    constructor() {
        if (isPlatformBrowser(this.platformId)) {
            // Este código solo se ejecuta en el navegador
            const savedTheme = localStorage.getItem('theme') as Theme | null;
            const systemTheme = this.getSystemTheme();

            // Lógica de inicialización:
            // 1. Usa el tema guardado si existe.
            // 2. Si no, usa el tema del sistema.
            this.theme.set(savedTheme || systemTheme);
        }

        // Este efecto se ejecuta cada vez que la señal `theme` cambia.
        effect(() => {
            const newTheme = this.theme();
            if (isPlatformBrowser(this.platformId)) {
                // Guarda la preferencia del usuario para futuras visitas.
                localStorage.setItem('theme', newTheme);
                // Aplica el tema al body del documento.
                this.document.documentElement.setAttribute(
                    'data-theme',
                    newTheme
                );
            }
        });
    }

    public toggleTheme(): void {
        this.theme.update((current) =>
            current === 'light' ? 'dark' : 'light'
        );
    }

    private getSystemTheme(): Theme {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }
}
