import {
    Component,
    HostListener,
    OnInit,
    signal,
    ChangeDetectionStrategy,
} from '@angular/core';

@Component({
    selector: 'app-back-to-top',
    imports: [],
    templateUrl: './back-to-top.html',
    styleUrl: './back-to-top.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BackToTop implements OnInit {
    showButton = signal<boolean>(false);
    scrollProgress = signal<number>(0);

    private scrollThreshold = 300;

    ngOnInit(): void {
        this.updateScrollState();
    }

    @HostListener('window:scroll', [])
    onWindowScroll(): void {
        this.updateScrollState();
    }

    private updateScrollState(): void {
        const scrollTop =
            window.pageYOffset || document.documentElement.scrollTop;
        const documentHeight =
            document.documentElement.scrollHeight -
            document.documentElement.clientHeight;

        // Mostrar/ocultar botón
        this.showButton.set(scrollTop > this.scrollThreshold);

        // Calcular progreso del scroll
        const progress = (scrollTop / documentHeight) * 100;
        this.scrollProgress.set(Math.min(progress, 100));
    }

    scrollToTop(): void {
        window.scrollTo({
            top: 0,
            behavior: 'smooth',
        });
    }
}
