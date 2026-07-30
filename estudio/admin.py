from django.contrib import admin
from .models import Sala, Ingeniero, Equipo, Reserva

# Registramos los nuevos modelos en el panel de administración
admin.site.register(Sala)
admin.site.register(Ingeniero)
admin.site.register(Equipo)
admin.site.register(Reserva)