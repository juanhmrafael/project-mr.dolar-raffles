import {
    Component,
    input,
    output,
    ChangeDetectionStrategy,
} from '@angular/core';
import {
    ContactInfo,
    FooterLink,
    NavLink,
    SocialLink,
} from '../../models/layout.types';
import { RouterLink } from '@angular/router';
import { NgOptimizedImage } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
@Component({
    selector: 'app-footer',
    imports: [RouterLink, NgOptimizedImage, LucideAngularModule],
    templateUrl: './footer.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Footer {
    public readonly termsClicked = output<void>();
    public readonly companyName = input.required<string>();
    public readonly tagline = input.required<string>();
    public readonly links = input<NavLink[]>();
    public readonly description = input.required<string>();
    public readonly quickLinks = input.required<FooterLink[]>();
    public readonly socialLinks = input.required<SocialLink[]>();
    public readonly contactInfo = input.required<ContactInfo>();
    public readonly logoUrl = input<string>();

    protected readonly currentYear = new Date().getFullYear();
}
