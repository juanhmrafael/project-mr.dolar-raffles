import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'padStart',
    standalone: true,
})
export class PadStartPipe implements PipeTransform {
    transform(value: string | number, totalLength: number, char = '0'): string {
        if (value == null) {
            return '';
        }
        return String(value).padStart(totalLength, char);
    }
}
