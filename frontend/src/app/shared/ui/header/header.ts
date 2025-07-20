import {
    Component,
    HostListener,
    input, output,
    signal,
    ChangeDetectionStrategy
} from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgOptimizedImage } from '@angular/common';
import { NavLink } from '../../models/layout.types';
import { User } from '../../models/user.types';

@Component({
    selector: 'app-header',
    imports: [RouterLink, RouterLinkActive, NgOptimizedImage],
    templateUrl: './header.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Header {
    public readonly logoUrl = input<string>();
    public readonly navLinks = input.required<NavLink[]>();
    public readonly theme = input.required<'light' | 'dark'>();

    public readonly themeToggleClicked = output<void>();
    public readonly logoutClicked = output<void>();

    public showMobileMenu = signal<boolean>(false);

    toggleMobileMenu(): void {
        this.showMobileMenu.update((show) => !show);
    }

    closeMobileMenu(): void {
        this.showMobileMenu.set(false);
    }

    // Cerrar menús al hacer click fuera o presionar Escape
    @HostListener('document:click', ['$event'])
    onDocumentClick(event: Event): void {
        const target = event.target as HTMLElement;

        // Cerrar mobile menu si click en backdrop
        if (
            this.showMobileMenu() &&
            target.classList.contains('backdrop-blur-sm')
        ) {
            this.showMobileMenu.set(false);
        }
    }

    @HostListener('document:keydown.escape')
    onEscapeKey(): void {
        this.showMobileMenu.set(false);
    }

    // Prevenir scroll cuando mobile menu está abierto
    @HostListener('document:keydown', ['$event'])
    onKeyDown(event: KeyboardEvent): void {
        if (
            this.showMobileMenu() &&
            (event.key === 'ArrowUp' || event.key === 'ArrowDown')
        ) {
            event.preventDefault();
        }
    }
}
