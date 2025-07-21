import { Component, ChangeDetectionStrategy, computed, effect, inject, input, model, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule, DecimalPipe } from '@angular/common';
import { catchError, of, timer, Subscription, map, } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';
import { toSignal } from '@angular/core/rxjs-interop';
// Imports de la aplicación
import { Modal } from '../modal/modal';
import { InputMaskDirective } from '../../directives/input-mask';
import { InputMasks } from '../../../core/masks/input-masks';
import { RafflesApi } from '../../../core/api/raffles-api';
import { EnhancedRaffleDetail } from '../../models/raffle';
import {
    PaymentMethod,
    ParticipationCreatePayload,
    ParticipationCreatedResponse,
    PaymentReportPayload,
    PaymentReportResponse,
} from '../../models/raffle';
import { TermsAndConditions } from '../terms-and-conditions/terms-and-conditions'; // ✅ IMPORTAR

type ParticipationStep =
    | 'personal'
    | 'tickets'
    | 'paymentMethod'
    | 'summary'
    | 'reserving'
    | 'paymentReport'
    | 'success';

@Component({
    selector: 'app-participation-modal',
    imports: [
        CommonModule,
        ReactiveFormsModule,
        DecimalPipe,
        LucideAngularModule,
        Modal,
        InputMaskDirective,
        TermsAndConditions,
    ],
    templateUrl: './participation-modal.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ParticipationModal {
    private readonly fb = inject(FormBuilder);
    private readonly rafflesApi = inject(RafflesApi);
    private countdownSubscription: Subscription | null = null;

    public readonly isOpen = model.required<boolean>();
    public readonly raffleDetail = input.required<EnhancedRaffleDetail>();

    protected readonly currentStep = signal<ParticipationStep>('personal');
    protected readonly ticketCount = signal(25);
    protected readonly selectedPaymentMethod = signal<PaymentMethod | null>(
        null
    );
    protected readonly termsAccepted = signal(false);
    protected readonly apiError = signal<string | null>(null);
    protected readonly formErrors = signal<{ [key: string]: string }>({});
    protected readonly participationResponse =
        signal<ParticipationCreatedResponse | null>(null);
    protected readonly countdown = signal(300);

    protected readonly personalDataForm = this.fb.group({
        full_name: ['', Validators.required],
        identification_number: [
            '',
            [Validators.required, Validators.pattern(/^[VEJGTPvejtgp]-\d+$/)],
        ],
        phone: ['', Validators.required],
        email: ['', [Validators.required, Validators.email]],
    });

    protected readonly paymentReportForm = this.fb.group({
        reference: ['', Validators.required],
        email: [''],
        binance_pay_id: [''],
        payment_date: [
            new Date().toISOString().split('T')[0],
            Validators.required,
        ],
    });

    protected readonly isPersonalDataFormValid = toSignal(
        this.personalDataForm.statusChanges.pipe(
            map((status) => status === 'VALID')
        ),
        { initialValue: this.personalDataForm.valid }
    );

    protected readonly isPaymentReportFormValid = toSignal(
        this.paymentReportForm.statusChanges.pipe(
            map((status) => status === 'VALID')
        ),
        { initialValue: this.paymentReportForm.valid }
    );

    protected readonly isCurrentStepValid = computed(() => {
        const step = this.currentStep();
        const raffle = this.raffleDetail();
        if (!raffle) return false;

        switch (step) {
            case 'personal':
                return this.isPersonalDataFormValid();
            case 'tickets':
                return (
                    this.ticketCount() >= raffle.min_ticket_purchase &&
                    this.ticketCount() <= 50
                );
            case 'paymentMethod':
                return !!this.selectedPaymentMethod();
            case 'summary':
                return this.termsAccepted();
            case 'paymentReport':
                return this.isPaymentReportFormValid();
            default:
                return true;
        }
    });

    protected readonly totalUSD = computed(
        () =>
            parseFloat(
                this.raffleDetail()?.unit_price_per_currency?.USD ?? '0'
            ) * this.ticketCount()
    );
    protected readonly totalVEF = computed(
        () =>
            parseFloat(
                this.raffleDetail()?.unit_price_per_currency?.VEF ?? '0'
            ) * this.ticketCount()
    );
    protected readonly countdownMinutes = computed(() =>
        Math.floor(this.countdown() / 60)
    );
    protected readonly countdownSeconds = computed(() => this.countdown() % 60);

    protected readonly InputMasks = InputMasks;
    protected readonly ticketShortcuts = [5, 10, 25, 50];
    protected readonly stepOrder: readonly ParticipationStep[] = [
        'personal',
        'paymentMethod',
        'tickets',
        'summary',
    ];
    protected readonly stepLabels: Record<string, string> = {
        personal: 'Datos Personales',
        paymentMethod: 'Método de Pago',
        tickets: 'Cantidad de Boletos',
        summary: 'Resumen y Confirmación',
    };
    constructor() {
        effect(() => {
            if (!this.isOpen()) {
                this.resetState();
            }
        });
    }

    protected nextStep(): void {
        if (!this.isCurrentStepValid()) return;
        this.apiError.set(null);
        this.formErrors.set({});
        const step = this.currentStep();
        if (step === 'personal') this.currentStep.set('paymentMethod');
        if (step === 'paymentMethod') this.currentStep.set('tickets');
        if (step === 'tickets') this.currentStep.set('summary');
    }

    protected previousStep(): void {
        this.apiError.set(null);
        this.formErrors.set({});
        const step = this.currentStep();
        if (step === 'paymentMethod') this.currentStep.set('personal');
        if (step === 'tickets') this.currentStep.set('paymentMethod');
        if (step === 'summary') this.currentStep.set('tickets');
    }

    protected changeTicketCount(amount: number): void {
        const current = this.ticketCount();
        const min = this.raffleDetail().min_ticket_purchase;
        const newCount = Math.max(min, Math.min(current + amount, 50));
        this.ticketCount.set(newCount);
    }

    protected setTicketCount(amount: number): void {
        this.ticketCount.set(amount);
    }

    protected reserveTickets(): void {
        if (!this.isCurrentStepValid()) return;
        this.currentStep.set('reserving');
        const formValue = this.personalDataForm.getRawValue();
        const payload: ParticipationCreatePayload = {
            raffle_id: this.raffleDetail().id,
            ticket_count: this.ticketCount(),
            full_name: formValue.full_name!,
            identification_number: formValue.identification_number!,
            phone: formValue.phone!,
            email: formValue.email!,
        };
        this.rafflesApi
            .createParticipation(payload)
            .pipe(
                catchError((err) => {
                    this.handleApiError(err.error);
                    this.currentStep.set('personal');
                    return of(null);
                })
            )
            .subscribe((response: ParticipationCreatedResponse | null) => {
                if (response) {
                    this.participationResponse.set(response);
                    this.currentStep.set('paymentReport');
                    this.startCountdown();
                }
            });
    }

    protected reportPayment(): void {
        if (!this.isCurrentStepValid()) return;
        const payload: PaymentReportPayload = {
            participation_id: this.participationResponse()!.id,
            payment_method_id: this.selectedPaymentMethod()!.id,
            payment_date: this.paymentReportForm.value.payment_date!,
            transaction_details: {
                reference: this.paymentReportForm.value.reference!,
                email: this.paymentReportForm.value.email || undefined,
                binance_pay_id:
                    this.paymentReportForm.value.binance_pay_id || undefined,
            },
        };
        this.rafflesApi
            .reportPayment(payload)
            .pipe(
                catchError((err) => {
                    this.handleApiError(err.error);
                    return of(null);
                })
            )
            .subscribe((response: PaymentReportResponse | null) => {
                if (response) {
                    this.stopCountdown();
                    this.currentStep.set('success');
                }
            });
    }

    private handleApiError(error: any): void {
        if (typeof error === 'object' && error !== null) {
            const fieldErrors: { [key: string]: string } = {};
            Object.keys(error).forEach((key) => {
                const message = Array.isArray(error[key])
                    ? error[key][0]
                    : String(error[key]);
                const control =
                    this.personalDataForm.get(key) ||
                    this.paymentReportForm.get(key);
                if (control) fieldErrors[key] = message;
                else this.apiError.set(message);
            });
            this.formErrors.set(fieldErrors);
        } else {
            this.apiError.set(error?.detail || 'Ocurrió un error inesperado.');
        }
    }

    private startCountdown(): void {
        this.countdownSubscription = timer(0, 1000).subscribe(() => {
            this.countdown.update((val) => {
                if (val > 0) return val - 1;
                this.isOpen.set(false);
                return 0;
            });
        });
    }

    private stopCountdown(): void {
        this.countdownSubscription?.unsubscribe();
        this.countdownSubscription = null;
    }

    private resetState(): void {
        this.currentStep.set('personal');
        this.personalDataForm.reset();
        this.paymentReportForm.reset({
            payment_date: new Date().toISOString().split('T')[0],
        });
        this.ticketCount.set(25);
        this.selectedPaymentMethod.set(null);
        this.termsAccepted.set(false);
        this.apiError.set(null);
        this.formErrors.set({});
        this.participationResponse.set(null);
        this.countdown.set(300);
        this.stopCountdown();
    }
}
