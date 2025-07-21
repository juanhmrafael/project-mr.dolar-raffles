// modal.ts
import {
    ChangeDetectionStrategy,
    Component,
    computed,
    effect,
    type ElementRef,
    inject,
    input,
    model,
    signal,
    viewChild,
    afterNextRender,
    DestroyRef,
    PLATFORM_ID,
    untracked,
    type OnInit,
} from '@angular/core';
import { isPlatformBrowser, NgClass } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

/** Interfaz para el estado consolidado del dispositivo y viewport. */
interface DeviceState {
    width: number;
    height: number;
    isKeyboardVisible: boolean;
    keyboardHeight: number;
    type: 'mobile' | 'tablet' | 'desktop';
    orientation: 'portrait' | 'landscape';
}

@Component({
    selector: 'app-modal',
    standalone: true,
    imports: [NgClass, LucideAngularModule],
    templateUrl: './modal.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Modal implements OnInit {
    // #region Injections
    private readonly destroyRef = inject(DestroyRef);
    private readonly platformId = inject(PLATFORM_ID);
    // #endregion

    // #region Inputs & Models
    public isOpen = model.required<boolean>();
    public title = input<string>();
    public size = input<'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'>('md');
    public mobileBehavior = input<'fullscreen' | 'bottom-sheet' | 'adaptive'>(
        'adaptive'
    );
    public closeOnBackdrop = input<boolean>(true);
    public closeOnEscape = input<boolean>(true);
    public maxHeight = input<string>();
    public padding = input<'none' | 'sm' | 'md' | 'lg'>('md');
    public preventBodyScroll = input<boolean>(true);
    // #endregion

    // #region ViewChild References
    private modalPanel = viewChild<ElementRef<HTMLDivElement>>('modalPanel');
    private modalContent = viewChild<ElementRef<HTMLElement>>('modalContent');
    // #endregion

    // #region State Signals
    private isAnimating = signal(false);
    private previousActiveElement = signal<HTMLElement | null>(null);
    private bodyScrollPosition = signal(0);
    protected deviceState = signal<DeviceState>({
        width: 0,
        height: 0,
        isKeyboardVisible: false,
        keyboardHeight: 0,
        type: 'desktop',
        orientation: 'portrait',
    });
    // #endregion

    // #region Computed Properties
    protected effectiveMobileBehavior = computed(() => {
        const behavior = this.mobileBehavior();
        const state = this.deviceState();
        if (behavior === 'adaptive') {
            if (state.type === 'mobile' && state.isKeyboardVisible)
                return 'bottom-sheet';
            if (state.type === 'mobile') return 'fullscreen';
            return 'fullscreen';
        }
        return behavior;
    });

    protected modalClasses = computed(() => {
        const size = this.size();
        const behavior = this.effectiveMobileBehavior();
        const state = this.deviceState();
        let base =
            'modal-panel relative flex flex-col bg-card/95 backdrop-blur-md text-card-foreground w-full overflow-hidden transition-all duration-300 border border-border/30 shadow-2xl shadow-black/20';

        if (behavior === 'fullscreen' && state.type === 'mobile') {
            base += ' rounded-none sm:rounded-2xl';
        } else if (behavior === 'bottom-sheet') {
            base += ' rounded-t-2xl sm:rounded-2xl';
        } else {
            base += ' rounded-xl sm:rounded-2xl lg:rounded-3xl';
        }

        const sizeClasses = {
            sm: 'sm:max-w-sm md:max-w-md',
            md: 'sm:max-w-md md:max-w-lg lg:max-w-xl',
            lg: 'sm:max-w-lg md:max-w-xl lg:max-w-2xl xl:max-w-3xl',
            xl: 'sm:max-w-xl md:max-w-2xl lg:max-w-4xl xl:max-w-5xl',
            '2xl': 'sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl',
            full: 'sm:max-w-full',
        };
        base += ` ${sizeClasses[size]}`;

        if (behavior === 'fullscreen' && state.type === 'mobile') {
            base += ' h-full max-h-full';
        } else {
            base += ' max-h-[90dvh]';
        }

        if (this.maxHeight()) {
            base += ` max-h-[${this.maxHeight()}]`;
        }

        if (behavior === 'bottom-sheet') {
            base += ' animate-modal-slide-up';
        } else {
            base += ' animate-modal-fade-in';
        }
        return base;
    });

    protected contentClasses = computed(
        () => 'modal-content flex-1 overflow-y-auto modal-scroll'
    );

    protected paddingClasses = computed(() => {
        const padding = this.padding();
        const type = this.deviceState().type;
        const paddingMap = {
            none: '',
            sm: type === 'mobile' ? 'p-3' : 'p-3 sm:p-4',
            md: type === 'mobile' ? 'p-4' : 'p-4 sm:p-6',
            lg: type === 'mobile' ? 'p-5' : 'p-6 sm:p-8',
        };
        return `${paddingMap[padding]} modal-safe-area`;
    });
    // #endregion

    constructor() {
        if (isPlatformBrowser(this.platformId)) {
            afterNextRender(() => {
                this.initializeDeviceAndViewportTracking();
            });
        }

        const modalPanelSignal = this.modalPanel;

        effect((onCleanup) => {
            const panelElementRef = modalPanelSignal();

            if (this.isOpen() && panelElementRef) {
                this.isAnimating.set(true);
                this.previousActiveElement.set(
                    document.activeElement as HTMLElement
                );
                this.preventBodyScrolling();

                const handleKeydown = (e: KeyboardEvent) =>
                    this.onDocumentKeydown(e);
                document.addEventListener('keydown', handleKeydown);

                const { observer, trapFocus } = this.setupFocusTrap(
                    panelElementRef.nativeElement
                );
                const focusTrapObserver = observer;
                document.addEventListener('keydown', trapFocus);

                setTimeout(() => this.isAnimating.set(false), 300);

                onCleanup(() => {
                    this.restoreBodyScrolling();
                    document.removeEventListener('keydown', handleKeydown);
                    document.removeEventListener('keydown', trapFocus);
                    focusTrapObserver?.disconnect();

                    const prevElement = untracked(this.previousActiveElement);
                    if (
                        prevElement &&
                        typeof prevElement.focus === 'function'
                    ) {
                        requestAnimationFrame(() =>
                            prevElement.focus({ preventScroll: true })
                        );
                    }
                });
            }
        });

        effect(() => {
            const { isKeyboardVisible, keyboardHeight } = this.deviceState();
            const property = '--keyboard-height';
            if (isKeyboardVisible) {
                document.documentElement.style.setProperty(
                    property,
                    `${keyboardHeight}px`
                );
            } else {
                document.documentElement.style.removeProperty(property);
            }
        });
    }

    ngOnInit(): void {
        if (isPlatformBrowser(this.platformId)) {
            this.deviceState.update((s) => ({
                ...s,
                width: window.innerWidth,
                height: window.innerHeight,
            }));
        }
    }

    // #region Initialization
    private initializeDeviceAndViewportTracking(): void {
        const visualViewport = window.visualViewport;

        const updateState = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const vvHeight = visualViewport?.height ?? height;
            const vvWidth = visualViewport?.width ?? width;

            const heightDiff = height - vvHeight;
            const isMobile = width < 768;
            const isKeyboardVisible = isMobile && heightDiff > 150;
            const keyboardHeight = isKeyboardVisible ? heightDiff : 0;

            this.deviceState.update((state) => ({
                ...state,
                width: vvWidth,
                height: vvHeight,
                isKeyboardVisible,
                keyboardHeight,
                type: isMobile ? 'mobile' : width < 1024 ? 'tablet' : 'desktop',
                orientation: height > width ? 'portrait' : 'landscape',
            }));

            if (isKeyboardVisible) {
                this.adjustScrollForKeyboard();
            }
        };

        if (visualViewport) {
            visualViewport.addEventListener('resize', updateState, {
                passive: true,
            });
            this.destroyRef.onDestroy(() =>
                visualViewport.removeEventListener('resize', updateState)
            );
        } else {
            window.addEventListener('resize', updateState, { passive: true });
            this.destroyRef.onDestroy(() =>
                window.removeEventListener('resize', updateState)
            );
        }

        updateState();
    }

    // ✅ CORRECCIÓN: Método de ajuste de scroll preciso y controlado.
    private adjustScrollForKeyboard(): void {
        const activeElement = document.activeElement as HTMLElement;
        const modalContent = this.modalContent()?.nativeElement;

        if (
            !activeElement ||
            !modalContent ||
            !modalContent.contains(activeElement)
        ) {
            return;
        }

        setTimeout(() => {
            const contentRect = modalContent.getBoundingClientRect();
            const elementRect = activeElement.getBoundingClientRect();

            if (
                elementRect.top >= contentRect.top &&
                elementRect.bottom <= contentRect.bottom
            ) {
                return;
            }

            const desiredPosition =
                activeElement.offsetTop - modalContent.clientHeight * 0.4;

            modalContent.scrollTo({
                top: desiredPosition,
                behavior: 'smooth',
            });
        }, 150);
    }
    // #endregion

    // #region Body Scroll Lock
    private preventBodyScrolling(): void {
        if (!this.preventBodyScroll()) return;
        this.bodyScrollPosition.set(window.scrollY);
        const scrollbarWidth =
            window.innerWidth - document.documentElement.clientWidth;
        const html = document.documentElement;
        html.style.setProperty('--scrollbar-width', `${scrollbarWidth}px`);
        html.classList.add('modal-open-html');
        const body = document.body;
        body.classList.add('modal-open-body');
        body.style.top = `-${this.bodyScrollPosition()}px`;
    }

    private restoreBodyScrolling(): void {
        if (!this.preventBodyScroll()) return;
        const html = document.documentElement;
        html.classList.remove('modal-open-html');
        html.style.removeProperty('--scrollbar-width');
        const body = document.body;
        body.classList.remove('modal-open-body');
        body.style.top = '';
        window.scrollTo(0, this.bodyScrollPosition());
    }
    // #endregion

    // #region Event Handlers
    private onDocumentKeydown(event: KeyboardEvent): void {
        if (event.key === 'Escape' && this.closeOnEscape()) {
            this.close();
        }
    }

    protected onBackdropClick(): void {
        if (this.closeOnBackdrop() && !this.isAnimating()) {
            this.close();
        }
    }

    protected close(): void {
        if (this.isAnimating()) return;
        this.isOpen.set(false);
    }
    // #endregion

    // #region Focus Trap
    private setupFocusTrap(panel: HTMLElement) {
        const getFocusable = () => this.getFocusableElements(panel);
        let focusableElements: HTMLElement[] = [];

        const trapFocus = (event: KeyboardEvent) => {
            if (event.key !== 'Tab' || focusableElements.length === 0) return;
            const first = focusableElements[0];
            const last = focusableElements[focusableElements.length - 1];
            const current = document.activeElement;
            if (event.shiftKey) {
                if (current === first) {
                    last.focus();
                    event.preventDefault();
                }
            } else {
                if (current === last) {
                    first.focus();
                    event.preventDefault();
                }
            }
        };

        const observer = new MutationObserver(() => {
            focusableElements = getFocusable();
        });
        observer.observe(panel, { childList: true, subtree: true });

        requestAnimationFrame(() => {
            focusableElements = getFocusable();
            focusableElements[0]?.focus();
        });

        return { observer, trapFocus };
    }

    private getFocusableElements(container: HTMLElement): HTMLElement[] {
        const selectors = [
            'a[href]:not([disabled])',
            'button:not([disabled])',
            "input:not([disabled]):not([type='hidden'])",
            'textarea:not([disabled])',
            'select:not([disabled])',
            'details > summary:first-of-type',
            "[tabindex]:not([tabindex='-1'])",
            "[contenteditable='true']",
        ].join(', ');

        return Array.from(
            container.querySelectorAll<HTMLElement>(selectors)
        ).filter((el) => el.offsetParent !== null);
    }
    // #endregion
}
