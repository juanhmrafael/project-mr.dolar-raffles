import {
    ChangeDetectionStrategy,
    Component,
    computed,
    effect,
    HostListener,
    input,
    model,
    ElementRef,
    viewChild,
    afterNextRender,
    DestroyRef,
    inject,
    signal,
    Injector,
    runInInjectionContext,
} from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { NgClass } from '@angular/common';

@Component({
    selector: 'app-modal',
    imports: [NgClass, LucideAngularModule],
    templateUrl: './modal.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Modal {
    private injector = inject(Injector);
    private destroyRef = inject(DestroyRef);

    // Estados de Doble Vía
    public isOpen = model.required<boolean>();

    // Inputs de Configuración
    public title = input<string>();
    public size = input<'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'>(
        'md'
    );
    public mobileBehavior = input<'fullscreen' | 'centered' | 'bottom-sheet'>(
        'fullscreen'
    );
    public closeOnBackdrop = input<boolean>(true);
    public closeOnEscape = input<boolean>(true);

    // ViewChild References
    private modalPanel = viewChild<ElementRef<HTMLDivElement>>('modalPanel');

    // Estados Internos
    private previousActiveElement = signal<Element | null>(null);
    private isInitialized = signal<boolean>(false);
    private isClosing = signal<boolean>(false);

    // Clases CSS mejoradas con bordes correctos
    protected modalClasses = computed(() => {
        const size = this.size();
        const mobileBehavior = this.mobileBehavior();

        // Clases base con bordes completamente redondeados
        const baseClasses = [
            'relative bg-card/95 backdrop-blur-xl',
            'shadow-floating border border-border',
            'ring-1 ring-primary/20',
            'overflow-hidden', // Para asegurar que los bordes redondeados funcionen correctamente
        ].join(' ');

        // Comportamiento móvil con bordes correctos
        const mobileClasses = {
            fullscreen: 'w-full h-full rounded-none sm:rounded-2xl',
            centered:
                'w-[90vw] max-w-[90vw] rounded-2xl mx-4 my-8 max-h-[80vh]',
            'bottom-sheet':
                'w-full rounded-t-3xl rounded-b-none mt-auto max-h-[85vh]',
        };

        // Tamaños responsivos con bordes consistentes
        const responsiveSizeClasses = {
            xs: 'sm:w-full sm:max-w-xs sm:rounded-2xl',
            sm: 'sm:w-full sm:max-w-sm sm:rounded-2xl',
            md: 'sm:w-full sm:max-w-md sm:rounded-2xl',
            lg: 'md:w-full md:max-w-2xl md:rounded-2xl',
            xl: 'lg:w-full lg:max-w-4xl lg:rounded-2xl',
            '2xl': 'xl:w-full xl:max-w-6xl xl:rounded-2xl',
            full: 'sm:w-[95vw] sm:h-[90vh] sm:max-w-none sm:rounded-2xl',
        };

        // Alturas responsivas
        const heightClasses = {
            fullscreen: 'sm:max-h-[90vh]',
            centered: 'sm:max-h-[85vh] md:max-h-[80vh]',
            'bottom-sheet': 'sm:max-h-[70vh] sm:rounded-2xl sm:mx-4 sm:mb-4',
        };

        return [
            baseClasses,
            mobileClasses[mobileBehavior],
            responsiveSizeClasses[size],
            heightClasses[mobileBehavior],
        ]
            .filter(Boolean)
            .join(' ');
    });

    // Clases para el contenedor principal
    protected containerClasses = computed(() => {
        const mobileBehavior = this.mobileBehavior();

        const baseClasses = 'fixed inset-0 z-modal flex p-0';

        const positionClasses = {
            fullscreen: 'items-center justify-center sm:p-6',
            centered: 'items-center justify-center p-4',
            'bottom-sheet': 'items-end justify-center sm:items-center sm:p-6',
        };

        return `${baseClasses} ${positionClasses[mobileBehavior]}`;
    });

    constructor() {
        afterNextRender(() => {
            this.isInitialized.set(true);
            runInInjectionContext(this.injector, () => {
                effect((onCleanup) => {
                    if (!this.isInitialized()) return;

                    const isModalOpen = this.isOpen();

                    if (isModalOpen) {
                        this.isClosing.set(false);
                        this.previousActiveElement.set(document.activeElement);

                        // Bloquear scroll del body con transición suave
                        const originalOverflow = document.body.style.overflow;
                        const originalPaddingRight =
                            document.body.style.paddingRight;

                        const scrollbarWidth =
                            window.innerWidth -
                            document.documentElement.clientWidth;
                        document.body.style.transition =
                            'padding-right 0.3s ease-out';
                        document.body.style.overflow = 'hidden';
                        document.body.style.paddingRight =
                            scrollbarWidth > 0 ? `${scrollbarWidth}px` : '';

                        // Configurar focus trap después de la animación
                        setTimeout(() => this.setupFocusTrap(), 300);

                        onCleanup(() => {
                            // Restaurar estilos con transición
                            document.body.style.transition =
                                'padding-right 0.3s ease-out';
                            document.body.style.overflow = originalOverflow;
                            document.body.style.paddingRight =
                                originalPaddingRight;

                            // Restaurar focus al elemento anterior
                            setTimeout(() => {
                                const prevElement =
                                    this.previousActiveElement();
                                if (
                                    prevElement &&
                                    prevElement instanceof HTMLElement
                                ) {
                                    prevElement.focus();
                                }
                            }, 100);
                        });
                    }
                });
            });
        });
    }

    @HostListener('document:keydown', ['$event'])
    protected onDocumentKeydown(event: KeyboardEvent): void {
        if (
            event.key === 'Escape' &&
            this.isOpen() &&
            this.closeOnEscape() &&
            !this.isClosing()
        ) {
            event.preventDefault();
            this.close();
        }
    }

    protected close(): void {
        if (this.isClosing()) return;

        this.isClosing.set(true);
        const panel = this.modalPanel();

        if (panel) {
            // Animación de salida suave
            panel.nativeElement.style.animation =
                'fade-out 0.2s ease-in forwards, scale-out 0.2s ease-in forwards';
        }

        // Cerrar después de la animación
        setTimeout(() => {
            this.isOpen.set(false);
            this.isClosing.set(false);
        }, 200);
    }

    protected onBackdropClick(): void {
        if (this.closeOnBackdrop() && !this.isClosing()) {
            // Efecto visual sutil de "shake" al hacer clic en el backdrop
            const panel = this.modalPanel();
            if (panel) {
                panel.nativeElement.style.animation = 'wiggle 0.3s ease-in-out';
                setTimeout(() => {
                    if (panel.nativeElement) {
                        panel.nativeElement.style.animation = '';
                    }
                }, 300);
            }

            setTimeout(() => this.close(), 100);
        }
    }

    private setupFocusTrap(): void {
        const panel = this.modalPanel();
        if (!panel) return;

        const focusableElements = this.getFocusableElements(
            panel.nativeElement
        );
        if (focusableElements.length === 0) return;

        focusableElements[0].focus();

        const trapFocusHandler = (event: KeyboardEvent) => {
            this.handleFocusTrap(event, focusableElements);
        };

        document.addEventListener('keydown', trapFocusHandler);

        this.destroyRef.onDestroy(() => {
            document.removeEventListener('keydown', trapFocusHandler);
        });
    }

    private getFocusableElements(container: HTMLElement): HTMLElement[] {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]',
            'details summary',
        ].join(', ');

        return Array.from(
            container.querySelectorAll(focusableSelectors)
        ).filter((element): element is HTMLElement => {
            const htmlElement = element as HTMLElement;
            return (
                htmlElement.offsetParent !== null &&
                !htmlElement.hasAttribute('disabled') &&
                htmlElement.tabIndex !== -1
            );
        });
    }

    private handleFocusTrap(
        event: KeyboardEvent,
        focusableElements: HTMLElement[]
    ): void {
        if (event.key !== 'Tab' || focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const activeElement = document.activeElement as HTMLElement;

        if (event.shiftKey) {
            if (activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            }
        } else {
            if (activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }
}
