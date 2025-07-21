import {
    Component,
    computed,
    input,
    output,
    ChangeDetectionStrategy,
} from '@angular/core';
import { SecondaryRaffle } from '../../models/raffle';
import { LucideAngularModule } from 'lucide-angular';
import { DatePipe, NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';

type IconName = 'Ticket' | 'Eye' | 'Trophy';

@Component({
    selector: 'app-raffle-card',
    imports: [DatePipe, NgOptimizedImage, LucideAngularModule, RouterLink],
    templateUrl: './raffle-card.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RaffleCard {
    public readonly raffle = input.required<SecondaryRaffle>();
    protected readonly lookupTicketsClicked = output<number>();

    protected onLookupClick(): void {
        this.lookupTicketsClicked.emit(this.raffle().id);
    }
    // La lógica ahora deriva directamente del 'winner_summary'
    public readonly winnerSummary = computed(
        () => this.raffle().winner_summary
    );

    public readonly mainWinnerInitial = computed<string>(
        () =>
            this.winnerSummary()?.main_winner_name.charAt(0).toUpperCase() ??
            '?'
    );

    public readonly buttonConfig = computed<{ text: string; icon: IconName }>(
        () => {
            switch (this.raffle().status) {
                case 'IN_PROGRESS':
                    return { text: 'Ver y Participar', icon: 'Ticket' };
                case 'PROCESSING_WINNERS':
                    return { text: 'Ver Sorteo', icon: 'Eye' };
                case 'FINISHED':
                    return { text: 'Ver Resultados', icon: 'Trophy' };
                default:
                    return { text: 'Ver Detalles', icon: 'Eye' };
            }
        }
    );
}
