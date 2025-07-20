export interface NavLink {
    label: string;
    path: string;
    icon?: string;
}

export type Theme = 'light' | 'dark';

export interface FooterLink {
    path: string;
    label: string;
    action?: 'openTermsModal';
}

export interface SocialLink {
    platform: string,
    url: string,
}

export interface ContactInfo {
    phone?: string
    email?: string
    address?: string
    hours?: string[]
}