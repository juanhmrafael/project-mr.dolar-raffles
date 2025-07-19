import { Component, ChangeDetectionStrategy, signal } from '@angular/core';
import { Modal } from '../../shared/ui/modal/modal';
import { LucideAngularModule } from 'lucide-angular';

@Component({
    selector: 'app-formulario-page',
    imports: [Modal, LucideAngularModule],
    templateUrl: './formulario-page.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormularioPage {
    // Signals para controlar cada instancia del modal
    modal = {
        terms: signal(false),
        form: signal(false),
        confirm: signal(false),
        sheet: signal(false),
    };
}
