/**
 * @file Contiene las interfaces para modelar los datos de la API de rifas.
 */

/**
 * Define los posibles estados de una rifa.
 */
export type RaffleStatus = 'IN_PROGRESS' | 'PROCESSING_WINNERS' | 'FINISHED';

// --- Tipos para Métodos de Pago (Unión Discriminada) ---

type PaymentMethodType = 'PAGO_MOVIL' | 'ZELLE' | 'BINANCE' | 'TRANSFERENCIA';
type Currency = 'VEF' | 'USD';

/**
 * Representa un único premio dentro de una rifa.
 */
export interface Prize {
    readonly level_title: string;
    readonly name: string;
    readonly display_order: number;
}

/**
 * Representa el resumen de los ganadores de una rifa finalizada.
 */
export interface WinnerSummary {
    readonly main_winner_name: string;
    readonly prize_won: string;
    readonly other_winners_count: number;
}

/**
 * Interfaz base que contiene los campos comunes a todas las rifas en la página principal.
 */
export interface RaffleBase {
    readonly id: number;
    readonly title: string;
    readonly slug: string;
    readonly image: string; // URL relativa
    readonly end_date: string | null; // Puede ser una fecha en formato ISO 8601 o null.
}

/**
 * Representa una rifa principal activa, con todos sus detalles promocionales.
 * Extiende la interfaz base.
 */
export interface MainRaffle extends RaffleBase {
    readonly promotional_message: string;
    readonly prizes: readonly Prize[];
}

/**
 * Representa una rifa en la lista secundaria, típicamente finalizada.
 * Extiende la interfaz base.
 */
export interface SecondaryRaffle extends RaffleBase {
    readonly status: RaffleStatus;
    readonly status_display: string; // Ej: "Finalizado", "Activo"
    readonly winner_summary: WinnerSummary | null; // Puede ser null si aún no hay ganadores
}

/**
 * Representa la estructura completa de la respuesta de la API para la página principal.
 * Esta es la interfaz principal que tu servicio de Angular debe esperar.
 */
/**
 * @file Contiene las interfaces para la respuesta del endpoint de la página principal.
 * @path GET /api/v1/main-page/
 */
export interface MainPageData {
    /**
     * La rifa principal actualmente activa.
     * Es `null` si no hay ninguna rifa principal en curso.
     */
    readonly main_raffle: MainRaffle | null;

    /**
     * Una lista de otras rifas, como las recientemente finalizadas.
     * Puede estar vacía.
     */
    readonly secondary_raffles: readonly SecondaryRaffle[];
}

export interface TimeLeft {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
    [key: string]: number;
}

interface BasePaymentMethod {
    readonly id: number;
    readonly name: string;
    readonly method_type: PaymentMethodType;
    readonly currency: Currency;
}

interface PagoMovilDetails {
    readonly bank: string; // Ej: "0102"
    readonly phone: string; // Ej: "(0424) 439-4932"
    readonly id_number: string; // Ej: "V-27718068"
}

interface ZelleDetails {
    readonly email: string;
    readonly holder_name: string;
}

interface BinanceDetails {
    readonly pay_id: string;
    readonly holder_name: string;
}

interface TransferenciaDetails {
    readonly bank: string;
    readonly id_number: string;
    readonly holder_name: string;
    readonly account_number: string;
}

// Unión Discriminada: El campo 'method_type' determina la forma de 'details'.
export type PaymentMethod = BasePaymentMethod &
    (
        | {
              readonly method_type: 'PAGO_MOVIL';
              readonly details: PagoMovilDetails;
          }
        | { readonly method_type: 'ZELLE'; readonly details: ZelleDetails }
        | { readonly method_type: 'BINANCE'; readonly details: BinanceDetails }
        | {
              readonly method_type: 'TRANSFERENCIA';
              readonly details: TransferenciaDetails;
          }
    );

// --- Interfaz Principal del Detalle de la Rifa ---
/**
 * @file Contiene las interfaces para la respuesta del endpoint de detalle de una rifa.
 * @path GET /api/v1/raffles/{slug}/
 */

export interface RaffleDetail {
    readonly id: number;
    readonly title: string;
    readonly slug: string;
    readonly description: string;
    readonly image: string;
    readonly currency: Currency;
    readonly ticket_price: string; // Se mantiene como string para precisión decimal.
    readonly min_ticket_purchase: number;
    readonly total_tickets: number;
    readonly status: RaffleStatus;
    readonly status_display: string;
    readonly start_date: string; // ISO 8601
    readonly end_date: string | null; // ISO 8601
    readonly prizes: readonly Prize[];
    readonly available_payment_methods: readonly PaymentMethod[];
}

/**
 * @file Contiene la interfaz para la respuesta del endpoint de estadísticas.
 * @path GET /api/v1/raffles/{slug}/stats/
 */
export interface RaffleStats {
    readonly tickets_available: number;
    readonly tickets_progress_percentage: string; // Se mantiene como string.
}

// --- Crear Participación ---

/**
 * Payload para crear una nueva participación.
 * @path POST /api/v1/participations/
 */
export interface ParticipationCreatePayload {
    raffle_id: number;
    full_name: string;
    phone: string; // Ej: "(0412) 123-4567"
    email: string;
    identification_number: string; // Ej: "V-27718068"
    ticket_count: number;
}

/**
 * Respuesta exitosa al crear una participación.
 */
export interface ParticipationCreatedResponse {
    readonly id: number; // ID de la Participación
    readonly ticket_count: number;
    readonly created_at: string; // ISO 8601
}

// --- Consultar Tickets ---

/**
 * Payload para buscar los tickets de un participante en una rifa.
 * @path POST /api/v1/tickets/lookup/
 */
export interface TicketLookupPayload {
    raffle_id: number;
    identification_number: string;
    phone: string;
    email: string;
}

/**
 * Representa un único ticket asignado a una participación.
 */
export interface AssignedTicket {
    readonly ticket_number: string;
    readonly assigned_at: string; // ISO 8601
}

/**
 * Define los posibles códigos de estado de un pago, incluyendo el estado
 * personalizado para participaciones que aún no han reportado un pago.
 * Estos códigos son estables, no cambian con la traducción y son seguros
 * para usar en la lógica de la UI (ej. en un switch o ngClass).
 */
export type PaymentStatusCode =
    | 'PENDING' // El pago fue reportado y está pendiente de verificación.
    | 'APPROVED' // El pago fue verificado y aprobado.
    | 'REJECTED' // El pago fue revisado y rechazado.
    | 'AWAITING_REPORT'; // Estado inicial, aún no se ha reportado un pago.

/**
 * Representa el objeto de estado de pago estructurado que devuelve la API.
 * Este diseño separa la lógica (code) de la presentación (display).
 */
export interface PaymentStatus {
    /**
     * El código de estado, inmutable y seguro para usar en la lógica (if, switch).
     */
    readonly code: PaymentStatusCode;

    /**
     * El texto de visualización, traducido y listo para mostrar directamente al usuario.
     * Ejemplo: "Aprobado", "Rechazado", "Pendiente de Verificación".
     */
    readonly display: string;
}

/**
 * Representa el estado completo de una participación encontrada.
 */
export interface ParticipationStatus {
    /**
     * El número de identificación del participante.
     * Ejemplo: "V-27718068"
     */
    readonly identification_number: string;
    /**
     * La fecha y hora en que se registró esta participación (lote de tickets).
     * Se presenta en formato ISO 8601.
     */
    readonly raffle_title: string;
    readonly created_at: string;
    readonly ticket_count: number;
    /**
     * La clave del estado del pago, para ser usada en la lógica de la aplicación (e.g., switch, ngIf).
     */

    /**
     * ✅ NUEVO CAMPO
     * Indica cuántos dígitos debe tener un número de ticket para su correcta
     * visualización con padding de ceros a la izquierda. Por ejemplo, un valor de 4
     * significa que el ticket '5' debe mostrarse como '0005'.
     * Este valor se deriva de la rifa a la que pertenece esta participación.
     */
    readonly ticket_number_digits: number;
    readonly payment_status: PaymentStatus;
    readonly tickets: readonly AssignedTicket[];
}

/**
 * La respuesta del endpoint de consulta de tickets es un array de estados de participación.
 */
export type TicketLookupResponse = readonly ParticipationStatus[];

/**
 * @file Contiene las interfaces para el cálculo y reporte de pagos.
 */

// --- API: Calcular Monto de Pago ---
// Path: POST /api/v1/payments/calculate-amount/

/**
 * Payload para la API de cálculo de monto de pago.
 */
export interface PaymentCalculationPayload {
    readonly raffle_id: number;
    readonly payment_method_id: number;
    readonly ticket_count: number;
}

/**
 * Respuesta de la API de cálculo de monto de pago.
 */
export interface PaymentCalculationResponse {
    /**
     * El monto final a pagar. Se representa como string para evitar
     * imprecisiones de punto flotante en JavaScript.
     */
    readonly amount_to_pay: string;

    /**
     * La moneda en la que se debe realizar el pago (ej: "VEF", "USD").
     */
    readonly currency: string;

    /**
     * La tasa de cambio que se utilizó para el cálculo, si aplica.
     * Es null si el pago es en la moneda base de la rifa.
     * Se representa como string para precisión decimal.
     */
    readonly exchange_rate_applied: string | null;
}

// --- API: Reportar un Nuevo Pago ---
// Path: POST /api/v1/payments/

/**
 * Define la estructura de los detalles de la transacción que el usuario debe proveer.
 * Las propiedades son opcionales porque varían según el método de pago.
 * La validación estricta de los campos requeridos se realiza en el backend.
 */
export interface TransactionDetails {
    /** Número de referencia o confirmación de la transacción. */
    reference: string;
    /** Email del titular (usado para Zelle). */
    email?: string;
    /** Binance Pay ID (usado para Binance). */
    binance_pay_id?: string;
}

/**
 * Payload para reportar un nuevo pago realizado por un usuario.
 */
export interface PaymentReportPayload {
    readonly participation_id: number;
    readonly payment_method_id: number;
    /**
     * Fecha en que se realizó el pago. Formato: "YYYY-MM-DD".
     */
    readonly payment_date: string;
    readonly transaction_details: TransactionDetails;
}

/**
 * Respuesta exitosa tras reportar un pago.
 */
export interface PaymentReportResponse {
    /**
     * Mensaje de estado localizado para mostrar al usuario.
     * Ej: "Pago reportado con éxito. En espera de verificación."
     */
    readonly status: string;
}
