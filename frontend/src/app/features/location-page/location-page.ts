import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import type { LocationInfo } from '../../shared/models/location';
import { Location } from '../../shared/ui/location/location';
import { LucideAngularModule } from 'lucide-angular';

@Component({
    selector: 'app-location-page',
    imports: [Location, LucideAngularModule],
    templateUrl: './location-page.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LocationPage {
    protected readonly location = signal<LocationInfo>({
        name: 'Mr. Dólar',
        address:
            'Entre Manrique y Cantaura, Calle Boyaca, Casa 94 21 Toldo Amarillo, Valencia 2001, Carabobo',
        phone: '(0424) 474-3384',
        googleMapsUrl: 'https://maps.app.goo.gl/9f66rh1vfoun2N8i9',
        googleMapsEmbedUrl:
            'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3927.0410650214217!2d-68.0012058!3d10.1773176!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e806722b77484e5%3A0x84750ebc8bf546a5!2smisterdolar1!5e0!3m2!1ses!2sve!4v1752878654857!5m2!1ses!2sve',
        hours: [
            { day: 'Lunes - Viernes', time: '8:00 AM - 8:00 PM' },
            { day: 'Sábados', time: '9:00 AM - 9:00 PM' },
            { day: 'Domingos', time: '10:00 AM - 6:00 PM' },
        ],
        features: ['Comida casera', 'Ambiente familiar', 'Pago en efectivo'],
        paymentInfo: 'Paga tus rifas en efectivo de forma segura.',
    });
}
