import { Component, ChangeDetectionStrategy } from '@angular/core';
import { createRafflesStore } from '../../core/state/raffles-store';
import { CurrentRaffle } from '../../shared/ui/current-raffle/current-raffle';
import { RaffleCard } from '../../shared/ui/raffle-card/raffle-card';
import { LucideAngularModule } from 'lucide-angular';

@Component({
    selector: 'app-home',
    imports: [CurrentRaffle, RaffleCard, LucideAngularModule],
    templateUrl: './home.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Home {
    protected readonly store = createRafflesStore();

    // protected readonly pastRaffles = signal<Raffle[]>([
    //     {
    //         id: 2,
    //         title: 'Rifa de Verano',
    //         prizes: [
    //             {
    //                 name: 'Premio Mayor',
    //                 value: '$10,000 USD',
    //             },
    //             {
    //                 name: '2do Premio',
    //                 value: 'Laptop de Última Generación',
    //             },
    //             {
    //                 name: '3er Premio',
    //                 value: 'Smartphone 5G',
    //             },
    //             {
    //                 name: '4to Premio',
    //                 value: 'Tarjeta de Regalo de $200',
    //             },
    //         ],
    //         description: 'Unas vacaciones soñadas.',
    //         endDate: new Date('2024-08-01'),
    //         imageUrl: 'assets/premio.webp',
    //         status: 'finished',
    //         winners: [
    //             {
    //                 name: 'Ana García',
    //                 prize: {
    //                     name: 'Premio Mayor',
    //                     value: 'PC Gamer de Alta Gama',
    //                 },
    //             },
    //             {
    //                 name: 'Carlos Rodríguez',
    //                 prize: { name: '2do Premio', value: 'Monitor Curvo 4K' },
    //             },
    //             {
    //                 name: 'Luisa Fernández',
    //                 prize: { name: '3er Premio', value: 'Silla Ergonómica' },
    //             },
    //         ],
    //     },
    //     {
    //         id: 3,
    //         title: 'Rifa Tecnológica',
    //         prizes: [
    //             {
    //                 name: 'Premio Mayor',
    //                 value: '$10,000 USD',
    //             },
    //             {
    //                 name: '2do Premio',
    //                 value: 'Laptop de Última Generación',
    //             },
    //             {
    //                 name: '3er Premio',
    //                 value: 'Smartphone 5G',
    //             },
    //             {
    //                 name: '4to Premio',
    //                 value: 'Tarjeta de Regalo de $200',
    //             },
    //         ],
    //         description: 'Lo último en tecnología.',
    //         endDate: new Date('2024-05-20'),
    //         imageUrl: 'assets/premio.webp',
    //         status: 'finished',
    //         winners: [
    //             {
    //                 name: 'Jorge Martinez',
    //                 prize: { name: 'Premio Único', value: 'iPhone 15 Pro' },
    //             },
    //         ],
    //     },
    //     {
    //         id: 4,
    //         title: 'Rifa de Regreso a Clases',
    //         prizes: [
    //             {
    //                 name: 'Premio Mayor',
    //                 value: '$10,000 USD',
    //             },
    //             {
    //                 name: '2do Premio',
    //                 value: 'Laptop de Última Generación',
    //             },
    //             {
    //                 name: '3er Premio',
    //                 value: 'Smartphone 5G',
    //             },
    //             {
    //                 name: '4to Premio',
    //                 value: 'Tarjeta de Regalo de $200',
    //             },
    //         ],
    //         description: 'El mejor equipo para tus estudios.',
    //         endDate: new Date('2024-02-10'),
    //         imageUrl: 'assets/premio.webp',
    //         status: 'finished',
    //         winners: [
    //             {
    //                 name: 'Sofia Vergara',
    //                 prize: {
    //                     name: 'Premio Principal',
    //                     value: 'MacBook Air M3',
    //                 },
    //             },
    //             {
    //                 name: 'David Ochoa',
    //                 prize: { name: 'Segundo Premio', value: 'iPad 10ma Gen' },
    //             },
    //         ],
    //     },
    // ]);
}
