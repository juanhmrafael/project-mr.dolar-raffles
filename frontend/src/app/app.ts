import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { LayoutConfig } from './core/services/layout-config';
import { MainLayout } from './layouts/main-layout/main-layout';

@Component({
    selector: 'app-root',
    imports: [MainLayout],
    templateUrl: './app.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
    private readonly layoutConfigService = inject(LayoutConfig);

    protected readonly navLinks = this.layoutConfigService.mainNavLinks;
    protected readonly user = this.layoutConfigService.currentUser;
    protected readonly logoUrl = this.layoutConfigService.appLogoUrl;
    protected readonly companyName = this.layoutConfigService.companyName;
    protected readonly currentTheme = this.layoutConfigService.theme;

    protected readonly footerTagline = this.layoutConfigService.footerTagline;
    protected readonly footerDescription =
        this.layoutConfigService.footerDescription;
    protected readonly footerLinks = this.layoutConfigService.footerLinks;
    protected readonly footerQuickLinks =
        this.layoutConfigService.footerQuickLinks;
    protected readonly footerSocialLinks =
        this.layoutConfigService.footerSocialLinks;
    protected readonly footerContactInfo =
        this.layoutConfigService.footerContactInfo;

    protected toggleTheme(): void {
        this.layoutConfigService.toggleTheme();
    }

    protected onLogout(): void {
        this.layoutConfigService.logout();
    }
}
