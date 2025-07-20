import { ChangeDetectionStrategy, Component } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
    selector: 'app-terms-and-conditions',
    imports: [LucideAngularModule],
    templateUrl: './terms-and-conditions.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TermsAndConditions {}
