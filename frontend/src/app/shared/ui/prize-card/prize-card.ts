import {
    Component,
    ChangeDetectionStrategy,
    computed,
    input,
} from '@angular/core';
import { NgOptimizedImage, CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Prize, RaffleStatus } from '../../models/raffle';

@Component({
    selector: 'app-prize-card',
    imports: [CommonModule, NgOptimizedImage, LucideAngularModule],
    templateUrl: './prize-card.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrizeCard {
    public readonly prize = input.required<Prize>();
    public readonly raffleStatus = input.required<RaffleStatus>();

    // Determina si debemos mostrar la vista del ganador.
    protected readonly isWinnerView = computed(() => {
        return this.raffleStatus() === 'FINISHED' && !!this.prize().winner_name;
    });

    // Elige qué imagen mostrar, dando prioridad a la de la entrega.
    protected readonly displayImage = computed(() => {
        const prize = this.prize();
        return prize.delivered_image ?? prize.image;
    });
}
