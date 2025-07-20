import { Component, ChangeDetectionStrategy, signal } from '@angular/core';
import { createRafflesStore } from '../../core/state/raffles-store';
import { CurrentRaffle } from '../../shared/ui/current-raffle/current-raffle';
import { RaffleCard } from '../../shared/ui/raffle-card/raffle-card';
import { LucideAngularModule } from 'lucide-angular';
import { TicketLookupModal } from '../../shared/ui/ticket-lookup-modal/ticket-lookup-modal';

@Component({
    selector: 'app-home',
    imports: [
        CurrentRaffle,
        RaffleCard,
        LucideAngularModule,
        TicketLookupModal,
    ],
    templateUrl: './home.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Home {
    protected readonly store = createRafflesStore();
    // --- AÑADIR ESTAS SEÑALES ---
    protected readonly isLookupModalOpen = signal(false);
    protected readonly selectedRaffleIdForLookup = signal<number | null>(null);

    // --- AÑADIR ESTE MÉTODO ---
    protected openTicketLookupModal(raffleId: number): void {
        this.selectedRaffleIdForLookup.set(raffleId);
        this.isLookupModalOpen.set(true);
    }
}
