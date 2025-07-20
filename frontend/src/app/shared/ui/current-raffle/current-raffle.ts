import {
    Component,
    computed,
    effect,
    input,
    signal,output,
    ChangeDetectionStrategy,
} from '@angular/core';
import { Prize, TimeLeft } from '../../models/raffle';
import { LucideAngularModule } from 'lucide-angular';
import { CommonModule, NgOptimizedImage } from '@angular/common';
import { EnhancedMainRaffle } from '../../../core/state/raffles-store';

@Component({
    selector: 'app-current-raffle',
    imports: [CommonModule, NgOptimizedImage, LucideAngularModule],
    templateUrl: './current-raffle.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CurrentRaffle {
    public readonly raffle = input.required<EnhancedMainRaffle>();
    protected readonly lookupTicketsClicked = output<number>();
    protected readonly timeLeft = signal<TimeLeft | null>(null);

    protected onLookupClick(): void {
        this.lookupTicketsClicked.emit(this.raffle().id);
    }
    
    public readonly mainPrize = computed<Prize | undefined>(() =>
        this.raffle().prizes.find((p) => p.display_order === 1)
    );

    public readonly otherPrizes = computed<readonly Prize[]>(() =>
        this.raffle()
            .prizes.filter((p) => p.display_order !== 1)
            .sort((a, b) => a.display_order - b.display_order)
    );

    public readonly progressPercentage = computed<number>(() => {
        const progress = this.raffle().stats?.tickets_progress_percentage;
        return progress ? parseFloat(progress) : 0;
    });

    protected readonly timeUnits = [
        { key: 'days', label: 'Días' },
        { key: 'hours', label: 'Horas' },
        { key: 'minutes', label: 'Min' },
        { key: 'seconds', label: 'Seg' },
    ] as const;

    constructor() {
        effect((onCleanup) => {
            const endDate = this.raffle().end_date;
            if (!endDate) return;

            const timer = setInterval(
                () => this.updateCountdown(endDate),
                1000
            );
            onCleanup(() => clearInterval(timer));
        });
    }

    private updateCountdown(endDate: string): void {
        const now = new Date().getTime();
        const distance = new Date(endDate).getTime() - new Date().getTime();

        if (distance < 0) {
            this.timeLeft.set({ days: 0, hours: 0, minutes: 0, seconds: 0 });
            return;
        }

        this.timeLeft.set({
            days: Math.floor(distance / (1000 * 60 * 60 * 24)),
            hours: Math.floor(
                (distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
            ),
            minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
            seconds: Math.floor((distance % (1000 * 60)) / 1000),
        });
    }
}
