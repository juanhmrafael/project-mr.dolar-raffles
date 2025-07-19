import {
    ChangeDetectionStrategy,
    Component,
    input,
    computed,
} from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { inject } from '@angular/core';
import { LocationInfo } from '../../models/location';
import { LucideAngularModule } from 'lucide-angular';
@Component({
    selector: 'app-location',
    imports: [LucideAngularModule],
    templateUrl: './location.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Location {
    private readonly sanitizer = inject(DomSanitizer);

    public readonly locationInfo = input.required<LocationInfo>();

    protected readonly safeMapUrl = computed(() => {
        const url = this.locationInfo().googleMapsEmbedUrl;
        return url ? this.sanitizer.bypassSecurityTrustResourceUrl(url) : null;
    });

    openInGoogleMaps() {
        if (this.locationInfo().googleMapsUrl) {
            window.open(this.locationInfo().googleMapsUrl, '_blank');
        }
    }
}
