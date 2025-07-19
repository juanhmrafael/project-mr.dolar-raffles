from django.contrib import admin

from .draw.admin import DrawAdmin
from .models import Draw, Prize, Raffle
from .prize.admin import PrizeAdmin
from .raffle.admin import RaffleAdmin

admin.site.register(Draw, DrawAdmin)
admin.site.register(Prize, PrizeAdmin)
admin.site.register(Raffle, RaffleAdmin)
