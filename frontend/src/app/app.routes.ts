import { Routes } from '@angular/router';

export const routes: Routes = [
    {
        path: '',
        title: 'Inicio - ¡Gana con Sandra!',
        loadComponent: () => import('./features/home/home').then((m) => m.Home),
    },
    {
        path: 'location',
        title: 'Ubicación - ¡Gana con Sandra!',
        loadComponent: () =>
            import('./features/location-page/location-page').then(
                (c) => c.LocationPage
            ),
    },
    {
        path: 'rifa/:slug',
        title: 'Detalles - ¡Gana con Sandra!',
        loadComponent: () =>
            import('./features/raffle-detail/raffle-detail').then(
                (m) => m.RaffleDetail
            ),
    },
    { path: '**', redirectTo: '' },
];
