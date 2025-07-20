import {
    Component,
    ChangeDetectionStrategy,
    input, model
} from '@angular/core';
import { Header } from '../../shared/ui/header/header';
import { Footer } from '../../shared/ui/footer/footer';
import { RouterOutlet } from '@angular/router';
import { BackToTop } from '../../shared/ui/back-to-top/back-to-top';
import { Modal } from '../../shared/ui/modal/modal';
import { TermsAndConditions } from '../../shared/ui/terms-and-conditions/terms-and-conditions';
import { LayoutStore } from '../../core/layout/layout-store';

@Component({
    selector: 'app-main-layout',
    imports: [
        RouterOutlet,
        Header,
        Footer,
        BackToTop,
        Modal,
        TermsAndConditions,
    ],
    templateUrl: './main-layout.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainLayout {
    public readonly config = input.required<LayoutStore>();
    // --- Estado del Modal de Términos ---
    protected isTermsModalOpen = model(false);
}
