import {
    Component,
    ChangeDetectionStrategy,
    input,
    output,
} from '@angular/core';
import { Header } from '../../shared/ui/header/header';
import { Footer } from '../../shared/ui/footer/footer';
import { RouterOutlet } from '@angular/router';
import {
    ContactInfo,
    FooterLink,
    NavLink,
    SocialLink,
} from '../../shared/models/layout.types';
import { User } from '../../shared/models/user.types';
import { BackToTop } from '../../shared/ui/back-to-top/back-to-top';

@Component({
    selector: 'app-main-layout',
    imports: [RouterOutlet, Header, Footer, BackToTop],
    templateUrl: './main-layout.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainLayout {
    // Header
    public readonly navLinks = input.required<NavLink[]>();
    public readonly user = input<User>();
    public readonly logoUrl = input<string>();
    public readonly companyName = input.required<string>();
    public readonly theme = input.required<'light' | 'dark'>();

    public readonly themeToggleClicked = output<void>();
    public readonly logoutClicked = output<void>();

    // Footer
    public readonly footerTagline = input.required<string>();
    public readonly footerDescription = input.required<string>();
    public readonly footerLinks = input.required<FooterLink[]>();
    public readonly footerQuickLinks = input.required<FooterLink[]>();
    public readonly footerSocialLinks = input.required<SocialLink[]>();
    public readonly footerContactInfo = input.required<ContactInfo>();
}
