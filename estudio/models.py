from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver


# ------------------------------------------
# 1. SALAS DE ENSAYO
# ------------------------------------------
class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_hora = models.DecimalField(max_digits=8, decimal_places=2)
    imagen = models.ImageField(upload_to='salas/', blank=True, null=True)

    def __str__(self):
        return self.nombre

# Borra la foto del disco cuando se elimina la sala
@receiver(post_delete, sender=Sala)
def borrar_imagen_sala(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(save=False)


# ------------------------------------------
# 2. INGENIEROS DE AUDIO
# ------------------------------------------
class Ingeniero(models.Model):
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    precio_hora = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    experiencia = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='ingenieros/', blank=True, null=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

# Borra la foto del disco cuando se elimina el ingeniero
@receiver(post_delete, sender=Ingeniero)
def borrar_imagen_ingeniero(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(save=False)


# ------------------------------------------
# 3. EQUIPOS (Micrófonos, Amplis, etc.)
# ------------------------------------------
# ------------------------------------------
# 3. EQUIPOS (Micrófonos, Amplis, etc.)
# ------------------------------------------
class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, default='General')
    precio_alquiler = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    imagen = models.ImageField(upload_to='equipos/', blank=True, null=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

# ✅ CORREGIDO: Eliminamos la línea de instance.comprobante
@receiver(post_delete, sender=Equipo)
def borrar_archivos_equipo(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(save=False)

# ------------------------------------------
# 4. RESERVAS (Conecta todo)
# ------------------------------------------
class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
    ]
    TIPO_CLIENTE = [
        ('BANDA', 'Banda Amateur'),
        ('PRO', 'Producción Profesional'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    ingeniero = models.ForeignKey(Ingeniero, on_delete=models.SET_NULL, null=True, blank=True)
    equipos = models.ManyToManyField(Equipo, blank=True)
    
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CLIENTE, default='BANDA')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    pagado = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Reserva {self.sala.nombre} - {self.usuario.username}"