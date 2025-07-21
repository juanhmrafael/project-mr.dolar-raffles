import {
    Component,
    ChangeDetectionStrategy,
    inject,
    signal,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { forkJoin, map, switchMap, catchError, EMPTY } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import {
    CommonModule,
    DatePipe,
    DecimalPipe,
    NgOptimizedImage,
} from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

// API & Models
import { RafflesApi } from '../../core/api/raffles-api';

// Components & Directives
import { PrizeCard } from '../../shared/ui/prize-card/prize-card';
import { TicketLookupModal } from '../../shared/ui/ticket-lookup-modal/ticket-lookup-modal';
import { ParticipationModal } from '../../shared/ui/participation-modal/participation-modal';

@Component({
    selector: 'app-raffle-detail',
    standalone: true,
    imports: [
        CommonModule,
        DatePipe,
        DecimalPipe,
        LucideAngularModule,
        PrizeCard,
        TicketLookupModal,
        NgOptimizedImage,
        ParticipationModal,
    ],
    templateUrl: './raffle-detail.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RaffleDetail {
    private readonly route = inject(ActivatedRoute);
    private readonly rafflesApi = inject(RafflesApi);
    private readonly router = inject(Router);

    // --- MODAL STATE ---
    protected readonly isLookupModalOpen = signal(false);
    protected isParticipationModalOpen = signal(false);
    
    // --- REACTIVE DATA FETCHING ---
    protected readonly raffle = toSignal(
        this.route.paramMap.pipe(
            switchMap((params) => {
                const slug = params.get('slug')!;
                return forkJoin({
                    detail: this.rafflesApi.getRaffleDetail(slug),
                    stats: this.rafflesApi.getRaffleStats(slug),
                }).pipe(
                    map(({ detail, stats }) => ({ ...detail, stats })),
                    catchError((err: HttpErrorResponse) => {
                        if (err.status === 404) {
                            this.router.navigate(['/']);
                        }
                        return EMPTY;
                    })
                );
            })
        )
    );
}
