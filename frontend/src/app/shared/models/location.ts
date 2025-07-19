export interface LocationInfo {
    name: string;
    address: string;
    phone: string;
    googleMapsUrl: string;
    googleMapsEmbedUrl: string;
    hours: {
        day: string;
        time: string;
    }[];
    features: string[];
    paymentInfo: string;
}
