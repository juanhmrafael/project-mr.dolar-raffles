import {
    Component,
    ChangeDetectionStrategy,
    inject,
    input,
    model,
    signal,
    effect,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, finalize, of } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';

// Imports de la aplicación
import { RafflesApi } from '../../../core/api/raffles-api';
import {
    TicketLookupResponse,
    TicketLookupPayload,
    PaymentStatusCode,
} from '../../models/raffle';
import { Modal } from '../modal/modal'; // Tu componente modal base
import { CommonModule, NgClass } from '@angular/common';
import { PadStartPipe } from '../../../core/pipes/pad-start';
// Definición de los estados de la vista para claridad
type ViewStatus = 'form' | 'loading' | 'success' | 'error';

@Component({
    selector: 'app-ticket-lookup-modal',
    imports: [
        CommonModule,
        NgClass,
        ReactiveFormsModule,
        LucideAngularModule,
        Modal,
        PadStartPipe, // Importamos tu componente modal
    ],
    templateUrl: './ticket-lookup-modal.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketLookupModal {
    // --- INJECTIONS ---
    private readonly fb = inject(FormBuilder);
    private readonly rafflesApi = inject(RafflesApi);

    // --- INPUTS & MODELS ---
    public readonly isOpen = model.required<boolean>();
    public readonly raffleId = input.required<number>();

    // --- STATE SIGNALS ---
    protected readonly viewStatus = signal<ViewStatus>('form');
    protected readonly lookupResult = signal<TicketLookupResponse | null>(null);
    protected readonly errorMessage = signal<string>('');

    constructor() {
        // ✅ Effect que se ejecuta cada vez que 'isOpen' cambia.
        effect(() => {
            // Si el modal pasa a estar cerrado (de true a false)...
            if (!this.isOpen()) {
                // ...resetea todo el estado a sus valores iniciales.
                // Usamos un setTimeout para evitar cambios de estado en el mismo ciclo.
                setTimeout(() => this.startNewLookup(), 0);
            }
        });
    }

    // --- FORM DEFINITION ---
    protected readonly lookupForm = this.fb.group({
        identification_type: ['V', [Validators.required]],
        identification_number_only: [
            '',
            [
                Validators.required,
                Validators.pattern(/^\d+$/),
                Validators.minLength(7),
            ],
        ],
        phone: ['', Validators.required],
        email: ['', [Validators.required, Validators.email]],
    });

    // --- PUBLIC METHODS ---

    /** Procesa el envío del formulario, llama a la API y maneja los estados. */
    protected onSubmit(): void {
        if (this.lookupForm.invalid) {
            this.lookupForm.markAllAsTouched();
            return;
        }

        this.viewStatus.set('loading');
        const formValue = this.lookupForm.getRawValue();

        const combinedIdentification = `${formValue.identification_type}-${formValue.identification_number_only}`;

        const payload: TicketLookupPayload = {
            raffle_id: this.raffleId(),
            identification_number: combinedIdentification,
            phone: formValue.phone!,
            email: formValue.email!,
        };
        this.rafflesApi
            .lookupTickets(payload)
            .pipe(
                catchError((err) => {
                    // Asumimos que el backend devuelve un mensaje de error útil
                    const message =
                        err?.error?.detail ||
                        'Ocurrió un error inesperado. Por favor, inténtalo de nuevo.';
                    this.errorMessage.set(message);
                    this.viewStatus.set('error');
                    return of(null); // Devuelve un observable nulo para que la cadena continúe
                }),
                finalize(() => {
                    if (this.viewStatus() === 'loading') {
                        // Si después del error/éxito seguimos en 'loading', algo falló, pasar a error.
                        this.viewStatus.set('error');
                        this.errorMessage.set(
                            'La respuesta del servidor no fue válida.'
                        );
                    }
                })
            )
            .subscribe((response) => {
                if (!response) return; // El error ya fue manejado en catchError

                if (response.length > 0) {
                    this.lookupResult.set(response);
                    this.viewStatus.set('success');
                } else {
                    this.errorMessage.set(
                        'No se encontraron participaciones con los datos ingresados. Verifica la información e inténtalo de nuevo.'
                    );
                    this.viewStatus.set('error');
                }
            });
    }

    /** Resetea el estado del modal para permitir una nueva consulta. */
    protected startNewLookup(): void {
        this.lookupForm.reset({ identification_type: 'V' });
        this.viewStatus.set('form');
        this.lookupResult.set(null);
        this.errorMessage.set('');
    }

    protected getPaymentStatusIcon(code: PaymentStatusCode): string {
        switch (code) {
            case 'APPROVED':
                return 'CheckCircle2';
            case 'PENDING':
                return 'Clock';
            case 'REJECTED':
                return 'XCircle';
            case 'AWAITING_REPORT':
                return 'HelpCircle';
            default:
                return 'AlertCircle';
        }
    }

    // Método adicional para obtener clases de badge más específicas
    protected getPaymentStatusBadgeClasses(code: string): string {
        const baseClasses =
            'inline-flex items-center gap-2 px-4 py-2 rounded-full font-bold text-sm transition-all duration-moderate';

        switch (code) {
            case 'APPROVED':
                return `${baseClasses} badge-success animate-bounce-in hover:scale-105`;
            case 'PENDING':
                return `${baseClasses} badge-warning animate-pulse hover:animate-wiggle`;
            case 'REJECTED':
                return `${baseClasses} badge-destructive hover:animate-wiggle`;
            case 'AWAITING_REPORT':
                return `${baseClasses} badge-info animate-float hover:animate-bounce`;
            default:
                return `${baseClasses} bg-muted text-muted-foreground`;
        }
    }
    // Método para obtener clases del contenedor del estado
    protected getPaymentStatusContainerClasses(code: string): string {
        const baseClasses =
            'rounded-xl p-4 border-2 transition-all duration-moderate hover:shadow-lg';

        switch (code) {
            case 'APPROVED':
                return `${baseClasses} bg-success/5 border-success/20 hover:bg-success/10 card-elevated`;
            case 'PENDING':
                return `${baseClasses} bg-warning/5 border-warning/20 hover:bg-warning/10 animate-pulse`;
            case 'REJECTED':
                return `${baseClasses} bg-destructive/5 border-destructive/20 hover:bg-destructive/10`;
            case 'AWAITING_REPORT':
                return `${baseClasses} bg-info/5 border-info/20 hover:bg-info/10 glass`;
            default:
                return `${baseClasses} bg-muted/5 border-muted/20`;
        }
    }
}
