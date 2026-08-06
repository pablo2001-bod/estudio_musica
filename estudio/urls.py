from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('salas/', views.salas_view, name='salas'),
    path('ingenieros/', views.ingenieros_view, name='ingenieros'),
    path('equipos/', views.equipos_view, name='equipos'),
    path('grid-ocupacion/', views.grid_ocupacion, name='grid_ocupacion'),

    path('api/reservas/', views.api_reservas, name='api_reservas'),
    path('api/reservas-eventos/', views.api_reservas_events, name='api_reservas_events'),
    path('reserva/crear/', views.crear_reserva, name='crear_reserva'),
    path('reserva/actualizar-fecha/', views.actualizar_fecha_reserva, name='actualizar_fecha_reserva'),
    path('reserva/agregar-equipo-extra/', views.agregar_equipo_extra, name='agregar_equipo_extra'),
    path('reserva/eliminar/<int:pk>/', views.eliminar_reserva, name='eliminar_reserva'),
    
    path('sala/crear/', views.crear_sala, name='crear_sala'),
    path('sala/editar/<int:sala_id>/', views.editar_sala, name='editar_sala'),
    path('sala/eliminar/<int:sala_id>/', views.eliminar_sala, name='eliminar_sala'),
    
    path('ingeniero/crear/', views.crear_ingeniero, name='crear_ingeniero'),
    path('ingeniero/editar/<int:ingeniero_id>/', views.editar_ingeniero, name='editar_ingeniero'),
    path('ingeniero/eliminar/<int:ingeniero_id>/', views.eliminar_ingeniero, name='eliminar_ingeniero'),
    
    path('equipo/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipo/editar/<int:equipo_id>/', views.editar_equipo, name='editar_equipo'),
    path('equipo/eliminar/<int:equipo_id>/', views.eliminar_equipo, name='eliminar_equipo'),
    
    path('reportes/', views.reportes_view, name='reportes'),
    path('reporte-salas/', views.reporte_salas, name='reporte_salas'),
    path('reporte-ingenieros/', views.reporte_ingenieros, name='reporte_ingenieros'),
    path('reportes/equipos/', views.reporte_equipos, name='reporte_equipos'),
    path('admin-reservas/', views.admin_reservas_view, name='admin_reservas'),
    path('reserva/cambiar-estado/<int:reserva_id>/<str:estado>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('gestion/', views.gestion_lista_view, name='gestion_lista'),
    
    path('login/', views.iniciar_sesion, name='login'),    
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard-reportes/', views.dashboard_reportes, name='dashboard_reportes'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/eliminar/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/estado/<int:usuario_id>/', views.alternar_estado_usuario, name='alternar_estado_usuario'),
    path('sw.js', TemplateView.as_view(
        template_name='estudio/sw.js', 
        content_type='application/javascript'
    ), name='sw.js'),
]