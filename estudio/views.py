from datetime import datetime, timedelta, date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, ProtectedError
from django.core.mail import send_mail
from django.conf import settings

from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField, FloatField
from django.db.models.functions import Coalesce

from .models import Sala, Ingeniero, Equipo, Reserva
from .forms import RegistroForm

def es_admin(user):
    return user.is_staff or user.is_superuser

def index(request):
    salas = Sala.objects.all()
    equipos = Equipo.objects.filter(disponible=True)
    ingenieros = Ingeniero.objects.filter(disponible=True)
    
    context = {
        'salas': salas,
        'equipos': equipos,
        'ingenieros': ingenieros,
    }
    return render(request, 'estudio/index.html', context)


def salas_view(request):
    salas = Sala.objects.all()
    return render(request, 'estudio/salas.html', {'salas': salas})


def ingenieros_view(request):
    ingenieros = Ingeniero.objects.all()
    return render(request, 'estudio/ingenieros.html', {'ingenieros': ingenieros})


def equipos_view(request):
    equipos = Equipo.objects.all()
    return render(request, 'estudio/equipos.html', {'equipos': equipos})

@login_required(login_url='login')
@user_passes_test(es_admin)
def crear_sala(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio_por_hora') or request.POST.get('precio_hora')
        imagen = request.FILES.get('imagen')
        
        Sala.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio_hora=precio,
            imagen=imagen
        )
        messages.success(request, 'Sala creada con éxito.')
        return redirect('salas')
    
    return render(request, 'estudio/crear_sala.html')

@login_required(login_url='login')
@user_passes_test(es_admin)
def editar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    
    if request.method == 'POST':
        sala.nombre = request.POST.get('nombre', sala.nombre)
        sala.descripcion = request.POST.get('descripcion', sala.descripcion)
        
        precio = request.POST.get('precio_por_hora') or request.POST.get('precio_hora')
        if precio:
            sala.precio_hora = precio

        if request.FILES.get('imagen'):
            if sala.imagen:
                sala.imagen.delete(save=False)
            sala.imagen = request.FILES.get('imagen')
            
        sala.save()
        messages.success(request, 'Sala actualizada correctamente.')
        return redirect('salas')
    
    return render(request, 'estudio/editar_sala.html', {'sala': sala})

@login_required(login_url='login')
@user_passes_test(es_admin)
def eliminar_sala(request, sala_id):
    if request.method == 'POST':
        sala = get_object_or_404(Sala, id=sala_id)
        if sala.imagen:
            sala.imagen.delete(save=False)
        sala.delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='login')
@user_passes_test(es_admin)
def crear_ingeniero(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        precio_hora = request.POST.get('precio_hora') or 0
        especialidad = request.POST.get('especialidad')
        experiencia = request.POST.get('experiencia')
        imagen = request.FILES.get('imagen')

        Ingeniero.objects.create(
            nombre=nombre,
            email=email,
            precio_hora=precio_hora,
            especialidad=especialidad,
            experiencia=experiencia,
            imagen=imagen,
            disponible=True
        )
        messages.success(request, 'Ingeniero registrado con éxito.')
        return redirect('ingenieros')

    return render(request, 'estudio/crear_ingeniero.html')

@login_required(login_url='login')
@user_passes_test(es_admin)
def editar_ingeniero(request, ingeniero_id):
    ingeniero = get_object_or_404(Ingeniero, id=ingeniero_id)
    
    if request.method == 'POST':
        ingeniero.nombre = request.POST.get('nombre', ingeniero.nombre)
        ingeniero.email = request.POST.get('email', ingeniero.email)
        
        precio = request.POST.get('precio_hora')
        if precio:
            ingeniero.precio_hora = precio
            
        ingeniero.especialidad = request.POST.get('especialidad', ingeniero.especialidad)
        ingeniero.experiencia = request.POST.get('experiencia', ingeniero.experiencia)
        
        if request.FILES.get('imagen'):
            if ingeniero.imagen:
                ingeniero.imagen.delete(save=False)
            ingeniero.imagen = request.FILES.get('imagen')
            
        ingeniero.save()
        messages.success(request, 'Datos del ingeniero actualizados.')
        return redirect('ingenieros')
    
    return render(request, 'estudio/editar_ingeniero.html', {'ingeniero': ingeniero})


@login_required(login_url='login')
@user_passes_test(es_admin)
def eliminar_ingeniero(request, ingeniero_id):
    if request.method == 'POST':
        ingeniero = get_object_or_404(Ingeniero, id=ingeniero_id)
        if ingeniero.imagen:
            ingeniero.imagen.delete(save=False)
        ingeniero.delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='login')
def crear_reserva(request):
    if request.method == 'POST':
        sala_id = request.POST.get('sala')
        ingeniero_id = request.POST.get('ingeniero')
        tipo_cliente = request.POST.get('tipo_cliente', 'REGULAR')
        fecha_inicio_str = request.POST.get('fecha_inicio')
        fecha_fin_str = request.POST.get('fecha_fin')
        equipos_ids = request.POST.getlist('equipos')

        if sala_id and fecha_inicio_str:
            fecha_inicio = datetime.fromisoformat(fecha_inicio_str)
            
            if fecha_fin_str:
                fecha_fin = datetime.fromisoformat(fecha_fin_str)
            else:
                fecha_fin = fecha_inicio + timedelta(hours=2)

            if fecha_fin <= fecha_inicio:
                mensaje_err = 'La fecha de fin debe ser posterior a la fecha de inicio.'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': mensaje_err}, status=400)
                messages.error(request, mensaje_err)
                return redirect('crear_reserva')

            cruces_sala = Reserva.objects.filter(
                sala_id=sala_id,
                estado__in=['Aprobada', 'Pendiente'],
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            if cruces_sala.exists():
                mensaje_err = 'La sala seleccionada ya está ocupada en ese rango de horario.'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': mensaje_err}, status=400)
                messages.error(request, mensaje_err)
                return redirect('crear_reserva')

            ingeniero = None
            if ingeniero_id:
                ingeniero = Ingeniero.objects.filter(id=ingeniero_id).first()
                if ingeniero:
                    cruces_ing = Reserva.objects.filter(
                        ingeniero_id=ingeniero_id,
                        estado__in=['Aprobada', 'Pendiente'],
                        fecha_inicio__lt=fecha_fin,
                        fecha_fin__gt=fecha_inicio
                    )
                    if cruces_ing.exists():
                        mensaje_err = f'El ingeniero {ingeniero.nombre} ya tiene un compromiso en ese rango de horario.'
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'status': 'error', 'message': mensaje_err}, status=400)
                        messages.error(request, mensaje_err)
                        return redirect('crear_reserva')

            duracion = fecha_fin - fecha_inicio
            horas = max(1, int(duracion.total_seconds() / 3600))

            sala = get_object_or_404(Sala, id=sala_id)

            total_sala = sala.precio_hora * horas
            total_ingeniero = (ingeniero.precio_hora * horas) if (ingeniero and hasattr(ingeniero, 'precio_hora')) else 0
            
            total_reserva = total_sala + total_ingeniero
            estado_inicial = 'Aprobada' if request.user.is_staff else 'Pendiente'

            reserva = Reserva.objects.create(
                usuario=request.user,
                sala=sala,
                ingeniero=ingeniero,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tipo_cliente=tipo_cliente,
                total=total_reserva,
                estado=estado_inicial
            )

            if equipos_ids:
                equipos = Equipo.objects.filter(id__in=equipos_ids)
                reserva.equipos.set(equipos)
                total_equipos = sum(eq.precio_alquiler for eq in equipos)
                reserva.total += total_equipos
                reserva.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'message': '¡Tu solicitud de reserva ha sido enviada con éxito! Queda a la espera de aprobación.'
                })

            messages.success(request, 'Solicitud de reserva enviada correctamente.')
            return redirect('index')

    salas = Sala.objects.all()
    ingenieros = Ingeniero.objects.filter(disponible=True) if hasattr(Ingeniero, 'disponible') else Ingeniero.objects.all()
    equipos = Equipo.objects.filter(disponible=True) if hasattr(Equipo, 'disponible') else Equipo.objects.all()

    return render(request, 'estudio/crear_reserva.html', {
        'salas': salas,
        'ingenieros': ingenieros,
        'equipos': equipos
    })

@login_required(login_url='login')
@user_passes_test(es_admin)
def cambiar_estado_reserva(request, reserva_id, estado):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    motivo = request.POST.get('motivo', '').strip() if request.method == 'POST' else ''

    reserva.estado = estado
    reserva.save()

    sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'estudio@talesstore.com')

    email_cliente = reserva.usuario.email
    if email_cliente:
        asunto_cliente = f"TaleStore - Actualización de tu Reserva #{reserva.id}"
        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        
        info_qr = (
            f"--- TALE STORE RESERVAS ---\n"
            f"Reserva ID: #{reserva.id}\n"
            f"Cliente: {nombre_cliente}\n"
            f"Sala: {reserva.sala.nombre}\n"
            f"Inicio: {reserva.fecha_inicio.strftime('%Y-%m-%d %H:%M')}\n"
            f"Fin: {reserva.fecha_fin.strftime('%Y-%m-%d %H:%M')}\n"
            f"Total: ${reserva.total}\n"
            f"Estado: {reserva.estado}"
        )
        
        qr_img = qrcode.make(info_qr)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        msg_plain = (
            f"Hola {nombre_cliente},\n\n"
            f"Estado de tu reserva para la sala '{reserva.sala.nombre}': {estado.upper()}.\n"
            f"Fecha Inicio: {reserva.fecha_inicio.strftime('%Y-%m-%d %H:%M')}\n"
            f"Fecha Fin: {reserva.fecha_fin.strftime('%Y-%m-%d %H:%M')}\n"
            f"Total: ${reserva.total}\n"
        )

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background-color: {'#28a745' if estado == 'Aprobada' else '#dc3545'}; padding: 20px; text-align: center; color: white;">
                <h2>TaleStore - Gestión de Reservas</h2>
                <p style="margin: 0; font-size: 18px;">Estado: <strong>{estado.upper()}</strong></p>
            </div>
            <div style="padding: 25px; background-color: #ffffff; color: #333333;">
                <p style="font-size: 16px;">Hola <strong>{nombre_cliente}</strong>,</p>
                {'<p>¡Tu reserva ha sido aprobada con éxito! Presenta este código QR al llegar al estudio.</p>' if estado == 'Aprobada' else f'<p>Lamentamos informarte que tu solicitud no pudo ser aprobada.<br><strong>Motivo:</strong> {motivo if motivo else "Mantenimiento u horario no disponible."}</p>'}
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <table style="width: 100%; font-size: 14px; line-height: 1.6;">
                    <tr><td><strong>Reserva ID:</strong></td><td>#{reserva.id}</td></tr>
                    <tr><td><strong>Sala:</strong></td><td>{reserva.sala.nombre}</td></tr>
                    <tr><td><strong>Fecha Inicio:</strong></td><td>{reserva.fecha_inicio.strftime('%Y-%m-%d %H:%M')}</td></tr>
                    <tr><td><strong>Fecha Fin:</strong></td><td>{reserva.fecha_fin.strftime('%Y-%m-%d %H:%M')}</td></tr>
                    <tr><td><strong>Total a Pagar:</strong></td><td>${reserva.total}</td></tr>
                </table>

                <div style="text-align: center; margin-top: 25px;">
                    <p style="font-size: 12px; color: #777; margin-bottom: 5px;">CÓDIGO QR DE CONFIRMACIÓN</p>
                    <img src="data:image/png;base64,{qr_b64}" alt="Código QR Reserva" style="width: 180px; height: 180px; border: 1px solid #ddd; padding: 5px; border-radius: 8px;">
                </div>
            </div>
            <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                TaleStore &copy; 2026 - Todos los derechos reservados.
            </div>
        </div>
        """

        try:
            email_msg = EmailMultiAlternatives(
                subject=asunto_cliente,
                body=msg_plain,
                from_email=sender_email,
                to=[email_cliente]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=True) # fail_silently evita que la app truene en la red de la casa si hay firewall
        except Exception as e:
            print(f" Aviso: No se pudo despachar el correo electrónico por conexión/puerto: {e}")

    # -------------------------------------------------------------
    # 2. NOTIFICACIÓN AL INGENIERO (SI LA RESERVA FUE APROBADA)
    # -------------------------------------------------------------
    if estado == 'Aprobada' and reserva.ingeniero and getattr(reserva.ingeniero, 'email', None):
        asunto_ing = f" ¡Nuevo Evento Asignado! - Sala {reserva.sala.nombre}"
        msg_ing = (
            f"Hola {reserva.ingeniero.nombre},\n\n"
            f"Se ha confirmado un evento en el que has sido asignado como ingeniero de audio:\n\n"
            f"Sala: {reserva.sala.nombre}\n"
            f"Cliente: {reserva.usuario.get_full_name() or reserva.usuario.username}\n"
            f"Fecha Inicio: {reserva.fecha_inicio.strftime('%d/%m/%Y %H:%M')}\n"
            f"Fecha Fin: {reserva.fecha_fin.strftime('%d/%m/%Y %H:%M')}\n\n"
            "Por favor, asegúrate de estar presente 15 minutos antes."
        )
        try:
            send_mail(
                asunto_ing,
                msg_ing,
                sender_email,
                [reserva.ingeniero.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Aviso: Error enviando al ingeniero: {e}")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'Reserva {estado.lower()} correctamente.'})

    messages.success(request, f'La reserva #{reserva.id} cambió a estado: {estado}.')
    return redirect('admin_reservas')

@login_required(login_url='login')
def actualizar_fecha_reserva(request):
    if request.method == 'POST':
        reserva_id = request.POST.get('id')
        nueva_fecha_str = request.POST.get('fecha_inicio')
        
        reserva = get_object_or_404(Reserva, id=reserva_id)

        if reserva.usuario == request.user or request.user.is_staff:
            nueva_fecha = datetime.fromisoformat(nueva_fecha_str.replace('Z', ''))
            duracion = reserva.fecha_fin - reserva.fecha_inicio
            nueva_fecha_fin = nueva_fecha + duracion

            # Validar que al arrastrar la fecha en FullCalendar tampoco choque con otra reserva
            cruces = Reserva.objects.filter(
                sala=reserva.sala,
                estado__in=['Aprobada', 'Pendiente'],
                fecha_inicio__lt=nueva_fecha_fin,
                fecha_fin__gt=nueva_fecha
            ).exclude(id=reserva.id)

            if cruces.exists():
                return JsonResponse({'status': 'error', 'message': 'No se puede mover: la sala ya está ocupada en ese horario.'}, status=400)

            reserva.fecha_inicio = nueva_fecha
            reserva.fecha_fin = nueva_fecha_fin
            reserva.save()
            return JsonResponse({'status': 'ok'})
            
        return HttpResponseForbidden("No tienes permiso")

@login_required(login_url='login')
def agregar_equipo_extra(request):
    if request.method == 'POST':
        equipo_id = request.POST.get('equipo_id')
        equipo = get_object_or_404(Equipo, id=equipo_id)

        reserva = Reserva.objects.filter(usuario=request.user).last()
        if reserva:
            reserva.equipos.add(equipo)
            reserva.total += equipo.precio_alquiler
            reserva.save()
            return JsonResponse({'status': 'ok', 'nuevo_total': reserva.total})
            
        return JsonResponse({'status': 'error', 'message': 'No hay reserva activa'}, status=400)

@login_required(login_url='login')
@user_passes_test(es_admin)
def eliminar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    reserva.delete()
    return JsonResponse({'status': 'ok'})

def api_reservas(request):
    reservas = Reserva.objects.all()
    eventos = []

    for res in reservas:
        if getattr(res, 'estado', '') == 'Pendiente':
            color = '#ffc107'
        elif getattr(res, 'estado', '') == 'Aprobada':
            color = '#28a745'
        elif getattr(res, 'estado', '') == 'Rechazada':
            color = '#dc3545'
        else:
            color = '#007bff' if res.tipo_cliente == 'PRO' else '#6c757d'

        eventos.append({
            'id': res.id,
            'title': f"{res.sala.nombre} - {res.usuario.username}",
            'start': res.fecha_inicio.isoformat(),
            'end': res.fecha_fin.isoformat(),
            'color': color
        })

    return JsonResponse(eventos, safe=False)

@login_required(login_url='login')
@user_passes_test(es_admin)
def admin_reservas_view(request):
    sala_id = request.GET.get('sala')
    
    if sala_id:
        reservas = Reserva.objects.filter(sala_id=sala_id).order_by('-id')
        sala_seleccionada = get_object_or_404(Sala, id=sala_id)
    else:
        reservas = Reserva.objects.all().order_by('-id')
        sala_seleccionada = None

    context = {
        'reservas': reservas,
        'sala_seleccionada': sala_seleccionada,
    }
    return render(request, 'estudio/admin_reservas.html', context)

@login_required(login_url='login')
@user_passes_test(es_admin)
def reporte_salas(request):
    salas = Sala.objects.all()
    total_salas = salas.count()
    fecha_hoy = date.today().strftime("%d/%m/%Y")
    
    context = {
        'salas': salas,
        'total_salas': total_salas,
        'fecha_hoy': fecha_hoy,
    }
    return render(request, 'estudio/reporte_salas.html', context)

@login_required(login_url='login')
@user_passes_test(es_admin)
def reporte_ingenieros(request):
    ingenieros = Ingeniero.objects.all()
    total_ingenieros = ingenieros.count()
    disponibles = ingenieros.filter(disponible=True).count()
    fecha_hoy = date.today().strftime("%d/%m/%Y")

    context = {
        'ingenieros': ingenieros,
        'total_ingenieros': total_ingenieros,
        'disponibles': disponibles,
        'fecha_hoy': fecha_hoy,
    }
    return render(request, 'estudio/reporte_ingenieros.html', context)

@login_required(login_url='login')
@user_passes_test(es_admin)
def reportes_view(request):
    reservas_bandas = Reserva.objects.filter(tipo_cliente='BANDA').count()
    reservas_pro = Reserva.objects.filter(tipo_cliente='PRO').count()
    ingresos_bandas = Reserva.objects.filter(tipo_cliente='BANDA').aggregate(Sum('total'))['total__sum'] or 0
    ingresos_pro = Reserva.objects.filter(tipo_cliente='PRO').aggregate(Sum('total'))['total__sum'] or 0
    
    equipos_populares = Equipo.objects.annotate(
        total_alquileres=Count('reserva'),
        ingreso_generado=Sum('reserva__total')
    ).order_by('-total_alquileres')

    context = {
        'reservas_bandas': reservas_bandas,
        'reservas_pro': reservas_pro,
        'ingresos_bandas': ingresos_bandas,
        'ingresos_pro': ingresos_pro,
        'equipos_populares': equipos_populares,
    }
    return render(request, 'estudio/reportes.html', context)

@login_required(login_url='login')
@user_passes_test(es_admin)
def gestion_lista_view(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo_registro')
        
        if tipo == 'sala':
            nombre = request.POST.get('nombre')
            precio = request.POST.get('precio')
            Sala.objects.create(nombre=nombre, precio_hora=precio)

        elif tipo == 'ingeniero':
            nombre = request.POST.get('nombre')
            especialidad = request.POST.get('especialidad')
            email = request.POST.get('email')
            Ingeniero.objects.create(nombre=nombre, especialidad=especialidad, email=email, disponible=True)

        elif tipo == 'equipo':
            nombre = request.POST.get('nombre')
            categoria = request.POST.get('categoria')
            precio = request.POST.get('precio')
            Equipo.objects.create(nombre=nombre, categoria=categoria, precio_alquiler=precio, disponible=True)

        messages.success(request, 'Elemento registrado correctamente.')
        return redirect('gestion_lista')

    salas = Sala.objects.all()
    ingenieros = Ingeniero.objects.all()
    equipos = Equipo.objects.all()

    context = {
        'salas': salas,
        'ingenieros': ingenieros,
        'equipos': equipos,
    }
    return render(request, 'estudio/gestion_lista.html', context)

def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url if next_url else 'index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, intenta de nuevo.')

    return render(request, 'registration/ingresar.html')

def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'registro.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'registro.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()

        messages.success(request, '¡Cuenta creada con éxito! Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'registration/registro.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('index')

@login_required(login_url='login')
@user_passes_test(es_admin)
def crear_equipo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria = request.POST.get('categoria')
        precio = request.POST.get('precio_alquiler')
        imagen = request.FILES.get('imagen')

        Equipo.objects.create(
            nombre=nombre,
            categoria=categoria,
            precio_alquiler=precio,
            imagen=imagen,
            disponible=True
        )
        messages.success(request, 'Equipo creado exitosamente.')
        return redirect('equipos')

    return render(request, 'estudio/crear_equipo.html')

@login_required(login_url='login')
@user_passes_test(es_admin)
def editar_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    
    if request.method == 'POST':
        equipo.nombre = request.POST.get('nombre', equipo.nombre)
        equipo.categoria = request.POST.get('categoria', equipo.categoria)
        equipo.precio_alquiler = request.POST.get('precio_alquiler', equipo.precio_alquiler)
        
        if request.FILES.get('imagen'):
            if equipo.imagen:
                equipo.imagen.delete(save=False)
            equipo.imagen = request.FILES.get('imagen')
            
        equipo.save()
        messages.success(request, 'Equipo actualizado correctamente.')
        return redirect('equipos')
    
    return render(request, 'estudio/editar_equipo.html', {'equipo': equipo})

@login_required(login_url='login')
@user_passes_test(es_admin)
def eliminar_equipo(request, equipo_id):
    if request.method == 'POST':
        equipo = get_object_or_404(Equipo, id=equipo_id)
        try:
            if hasattr(equipo, 'reserva_set'):
                equipo.reserva_set.clear()

            equipo.delete()
            return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)

@login_required(login_url='login')
@user_passes_test(es_admin)
def reporte_equipos(request):
    equipos = Equipo.objects.annotate(total_alquileres=Count('reserva'))
    total_equipos = equipos.count()
    disponibles = equipos.filter(disponible=True).count()
    fecha_hoy = date.today().strftime("%d/%m/%Y")

    context = {
        'equipos': equipos,
        'total_equipos': total_equipos,
        'disponibles': disponibles,
        'fecha_hoy': fecha_hoy,
    }
    return render(request, 'estudio/reporte_equipos.html', context)

@login_required(login_url='login')
def grid_ocupacion(request):
    return render(request, 'estudio/grid_ocupacion.html')

@login_required(login_url='login')
def api_reservas_events(request):
    reservas = Reserva.objects.select_related('sala', 'usuario').all()
    eventos = []
    
    for r in reservas:
        eventos.append({
            'id': r.id,
            'title': f"{r.sala.nombre} - {r.usuario.username}",
            'start': r.fecha_inicio.isoformat(),
            'end': r.fecha_fin.isoformat(),
            'color': '#198754' if r.estado == 'Aprobada' else ('#ffc107' if r.estado == 'Pendiente' else '#dc3545'),
            'textColor': '#000' if r.estado == 'Pendiente' else '#fff'
        })
        
    return JsonResponse(eventos, safe=False)


@login_required(login_url='login')
@user_passes_test(es_admin)
def dashboard_reportes(request):
    # -------------------------------------------------------------
    # 1. HORAS DE USO POR TIPO DE CLIENTE (REGULAR vs PRO)
    # -------------------------------------------------------------
    reservas_aprobadas = Reserva.objects.filter(estado='Aprobada')

    horas_regular = 0
    horas_pro = 0

    for r in reservas_aprobadas:
        duracion_horas = max(1, int((r.fecha_fin - r.fecha_inicio).total_seconds() / 3600))
        tipo = getattr(r, 'tipo_cliente', 'REGULAR')
        if tipo == 'PRO':
            horas_pro += duracion_horas
        else:
            horas_regular += duracion_horas

    # -------------------------------------------------------------
    # 2. RENTABILIDAD DE EQUIPOS ALQUILADOS (Procesado en Python)
    # -------------------------------------------------------------
    equipos = Equipo.objects.all()
    equipos_rentabilidad = []

    for eq in equipos:
        # Contar cuántas reservas APROBADAS incluyen este equipo
        veces = eq.reserva_set.filter(estado='Aprobada').count()
        
        # Calcular recaudado sumando con seguridad los tipos
        precio = float(eq.precio_alquiler or 0)
        recaudado = veces * precio

        equipos_rentabilidad.append({
            'nombre': eq.nombre,
            'precio_alquiler': eq.precio_alquiler,
            'veces_alquilado': veces,
            'total_recaudado': recaudado,
        })

    # Ordenar los equipos de mayor a menor rentabilidad
    equipos_rentabilidad = sorted(equipos_rentabilidad, key=lambda x: x['total_recaudado'], reverse=True)

    # Métricas generales
    total_ingresos_reservas = sum(float(r.total or 0) for r in reservas_aprobadas)
    total_reservas_cont = reservas_aprobadas.count()

    context = {
        'horas_regular': horas_regular,
        'horas_pro': horas_pro,
        'equipos_rentabilidad': equipos_rentabilidad,
        'total_ingresos': total_ingresos_reservas,
        'total_reservas_cont': total_reservas_cont,
    }

    return render(request, 'estudio/dashboard_reportes.html', context)