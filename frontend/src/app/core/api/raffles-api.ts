import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    MainPageData,
    RaffleStats,
    TicketLookupPayload,
    TicketLookupResponse,
} from '../../shared/models/raffle';

@Injectable({
    providedIn: 'root',
})
export class RafflesApi {
    private readonly http = inject(HttpClient);

    public getMainPageData(): Observable<MainPageData> {
        return this.http.get<MainPageData>('/api/v1/main-page/');
    }

    // ✅ NUEVO MÉTODO
    public getRaffleStats(slug: string): Observable<RaffleStats> {
        return this.http.get<RaffleStats>(`/api/v1/raffles/${slug}/stats/`);
    }

    /**
     * Makes a POST request to look up participant tickets for a given raffle.
     * @param payload The data required for ticket lookup.
     * @returns An observable emitting the lookup results.
     */
    public lookupTickets(
        payload: TicketLookupPayload
    ): Observable<TicketLookupResponse> {
        return this.http.post<TicketLookupResponse>(
            '/api/v1/tickets/lookup/',
            payload
        );
    }
}
