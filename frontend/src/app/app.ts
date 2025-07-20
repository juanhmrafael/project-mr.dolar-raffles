import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { LayoutStore } from './core/layout/layout-store';
import { MainLayout } from './layouts/main-layout/main-layout';

@Component({
    selector: 'app-root',
    imports: [MainLayout],
    templateUrl: './app.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
    protected readonly layoutStore = inject(LayoutStore);
}
