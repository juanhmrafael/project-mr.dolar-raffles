// Ruta: /src/app/shared/directives/input-mask.ts

import { Directive, ElementRef, Input, OnInit, inject } from '@angular/core';
import Inputmask from 'inputmask';

@Directive({
    selector: '[inputMask]',
    standalone: true,
})
export class InputMaskDirective implements OnInit {
    // Inyectamos una referencia al elemento <input> donde se aplica la directiva.
    private readonly elementRef = inject(ElementRef<HTMLInputElement>);

    // Usamos Inputmask.Options para acceder al tipo correcto desde el namespace.
    @Input('inputMask')
    public options: Inputmask.Options = {};

    public ngOnInit(): void {
        // Cuando el componente se inicializa, aplicamos la máscara al elemento.
        Inputmask(this.options).mask(this.elementRef.nativeElement);
    }
}
