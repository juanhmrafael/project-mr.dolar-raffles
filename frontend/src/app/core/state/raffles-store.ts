// src/app/core/state/raffles-store.ts
import { computed, inject, Signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RafflesApi } from '../api/raffles-api';
import { MainRaffle, RaffleStats } from '../../shared/models/raffle';
import { from, of, switchMap } from 'rxjs';

// Creamos un nuevo tipo para el objeto combinado que usará la UI
export type EnhancedMainRaffle = MainRaffle & { stats: RaffleStats | null };

export function createRafflesStore() {
    const api = inject(RafflesApi);
    const mainPageData$ = toSignal(api.getMainPageData());

    const mainRaffle$ = computed(() => mainPageData$()?.main_raffle ?? null);

    // El nombre de la señal ahora coincide con la propiedad de la API (en camelCase)
    const secondaryRaffles$ = computed(
        () => mainPageData$()?.secondary_raffles ?? []
    );

    // Cadena reactiva: Obtiene las estadísticas cada vez que `mainRaffle$` cambia.
    const mainRaffleStats$ = toSignal(
        // Se convierte la señal en un Observable para usar `pipe`
        toObservable(mainRaffle$).pipe(
            switchMap((raffle) =>
                raffle ? api.getRaffleStats(raffle.slug) : of(null)
            )
        ),
        // SE PROVEE UN VALOR INICIAL para evitar `undefined`
        { initialValue: null }
    );

    // SEÑAL COMBINADA: La UI consumirá esta señal, que ya tiene todo.
    const enhancedMainRaffle$ = computed(() => {
        const raffle = mainRaffle$();
        const stats = mainRaffleStats$();
        // El tipo de `stats` ahora es `RaffleStats | null`, lo que es compatible.
        return raffle ? { ...raffle, stats } : null;
    });

    return {
        mainRaffle: enhancedMainRaffle$, // La UI usa este nombre simple
        secondaryRaffles: secondaryRaffles$,
        hasNoRaffles: computed(
            () => !mainRaffle$() && secondaryRaffles$().length === 0
        ),
    };
}
