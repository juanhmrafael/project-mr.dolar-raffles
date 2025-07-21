import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    MainPageData,
    RaffleStats,
    TicketLookupPayload,
    TicketLookupResponse,
    RaffleDetail,
    ParticipationCreatePayload,
    ParticipationCreatedResponse,
    PaymentReportPayload,
    PaymentReportResponse,
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

    public getRaffleDetail(slug: string): Observable<RaffleDetail> {
        return this.http.get<RaffleDetail>(`/api/v1/raffles/${slug}/`);
    }

    /**
     * Crea una nueva participación para una rifa.
     * @path POST /api/v1/participations/
     */
    public createParticipation(
        payload: ParticipationCreatePayload
    ): Observable<ParticipationCreatedResponse> {
        return this.http.post<ParticipationCreatedResponse>(
            '/api/v1/participations/',
            payload
        );
    }

    /**
     * Reporta un pago para una participación existente.
     * @path POST /api/v1/payments/
     */
    public reportPayment(
        payload: PaymentReportPayload
    ): Observable<PaymentReportResponse> {
        return this.http.post<PaymentReportResponse>(
            '/api/v1/payments/',
            payload
        );
    }
}
