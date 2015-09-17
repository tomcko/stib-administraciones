from django.conf.urls import patterns, url

from .views import (EstablecerTipoComunicacion,
                    NotificarProductosUsuarios,
                    NotificarServiciosUsuarios,
                    get_autocomplete_result,
                    NotificarProductosEdificios,
                    get_autocomplete_edificios_result,
                    NotificarServiciosEdificios,
                    listar_notificaciones_admnistraciones,
                    listar_notificaciones_edificios,
                    NotificacionesEdificiosProductosDeleteView,
                    NotificacionesEdificiosServiciosDeleteView,
                    NotificacionesAdministracionesProductosDeleteView,
                    NotificacionesAdministracionesServiciosDeleteView,
                    reenviar_email_edificios_productos,
                    reenviar_email_edificios_servicios,
                    reenviar_email_administraciones_productos,
                    reenviar_email_administraciones_servicios,
                    NotificacionesEdificiosServiciosDetailView,
                    NotificacionesEdificiosProductosDetailView,
                    edificios_cambio_estado_productos,
                    edificios_cambio_estado_servicios,
                    NotificacionesAdministracionesServiciosDetailView,
                    NotificacionesAdministracionesProductosDetailView,
                    administraciones_cambio_estado_productos,
                    administraciones_cambio_estado_servicios,
                    notificiones_edificio)
urlpatterns = patterns('',
                       url(
                           regex=r'^$',
                           view=EstablecerTipoComunicacion.as_view(),
                           name='definir'
                       ),
                       url(
                           regex=r'^productos-administraciones$',
                           view=NotificarProductosUsuarios.as_view(),
                           name='productos-administraciones'
                       ),
                       url(
                           regex=r'^search-autocomplete/$',
                           view=get_autocomplete_result,
                           name='search_autocomplete'
                       ),
                       url(
                           regex=r'^servicios-administraciones$',
                           view=NotificarServiciosUsuarios.as_view(),
                           name='servicios-administraciones'
                       ),
                       url(
                           regex=r'^productos-edificios$',
                           view=NotificarProductosEdificios.as_view(),
                           name='productos-edificios'
                       ),
                       url(
                           regex=r'^servicios-edificios$',
                           view=NotificarServiciosEdificios.as_view(),
                           name='servicios-edificios'
                       ),
                       url(
                           regex=r'^search-autocomplete-edificios$',
                           view=get_autocomplete_edificios_result,
                           name='search-autocomplete-edificios'
                       ),
                       # -- lista todas las notificaciones de edificios
                       # -- para ser consultadas desde el Backend
                       url(
                           regex=r'^edificios/list$',
                           view=listar_notificaciones_edificios,
                           name='edificios-list'
                       ),
                       # -- lista todas las notificaciones de las adminsitraciones
                       # -- para ser consultadas desde el Backend
                       url(
                           regex=r'^administraciones/list$',
                           view=listar_notificaciones_admnistraciones,
                           name='administraciones-list'
                       ),
                       # -- lista todas las notificaciones de UN EDIFICIO
                       # -- para ser consultadas por las administraciones
                       url(
                           regex=r'^edificios/list/(?P<edificio>\d+)$',
                           view=notificiones_edificio,
                           name='edificio-list'
                       ),
                       url(
                           regex=r'^edificios/productos/delete/(?P<pk>\d+)$',
                           view=NotificacionesEdificiosProductosDeleteView.as_view(),
                           name='delete-edificios-productos'
                       ),
                       url(
                           regex=r'^edificios/servicios/delete/(?P<pk>\d+)$',
                           view=NotificacionesEdificiosServiciosDeleteView.as_view(),
                           name='delete-edificios-servicios'
                       ),
                       url(
                           regex=r'^administraciones/productos/delete/(?P<pk>\d+)$',
                           view=NotificacionesAdministracionesProductosDeleteView.as_view(),
                           name='delete-administraciones-productos'
                       ),
                       url(
                           regex=r'^administraciones/servicios/delete/(?P<pk>\d+)$',
                           view=NotificacionesAdministracionesServiciosDeleteView.as_view(),
                           name='delete-administraciones-servicios'
                       ),
                       url(
                           regex=r'^reenviar/mail/edificios/productos/(?P<notificacion>\d+)$',
                           view=reenviar_email_edificios_productos,
                           name='reenviar-mail-edificios-productos'
                       ),
                       url(
                           regex=r'^reenviar/mail/edificios/servicios/(?P<notificacion>\d+)$',
                           view=reenviar_email_edificios_servicios,
                           name='reenviar-mail-edificios-servicios'
                       ),
                       url(
                           regex=r'^reenviar/mail/administraciones/productos/(?P<notificacion>\d+)$',
                           view=reenviar_email_administraciones_productos,
                           name='reenviar-mail-administraciones-productos'
                       ),
                       url(
                           regex=r'^reenviar/mail/administraciones/servicios/(?P<notificacion>\d+)$',
                           view=reenviar_email_administraciones_servicios,
                           name='reenviar-mail-administraciones-servicios'
                       ),
                       url(
                           regex=r'^edificios/servicios/detail/(?P<pk>\d+)$',
                           view=NotificacionesEdificiosServiciosDetailView.as_view(),
                           name='edificios-servicios-detail'
                       ),
                       url(
                           regex=r'^edificios/productos/detail/(?P<pk>\d+)$',
                           view=NotificacionesEdificiosProductosDetailView.as_view(),
                           name='edificios-productos-detail'
                       ),
                       url(
                           regex=r'^edificios/productos/cambio/estado$',
                           view=edificios_cambio_estado_productos,
                           name='cambio-estado-productos'
                       ),
                       url(
                           regex=r'^edificios/servicios/cambio/estado$',
                           view=edificios_cambio_estado_servicios,
                           name='cambio-estado-servicios'
                       ),
                       url(
                           regex=r'^administraciones/productos/detail/(?P<pk>\d+)$',
                           view=NotificacionesAdministracionesProductosDetailView.as_view(),
                           name='administraciones-productos-detail'
                       ),
                        url(
                           regex=r'^administraciones/servicios/detail/(?P<pk>\d+)$',
                           view=NotificacionesAdministracionesServiciosDetailView.as_view(),
                           name='administraciones-servicios-detail'
                       ),
                       url(
                           regex=r'^administraciones/productos/cambio/estado$',
                           view=administraciones_cambio_estado_productos,
                           name='administraciones-cambio-estado-productos'
                       ),
                       url(
                           regex=r'^administraciones/servicios/cambio/estado$',
                           view=administraciones_cambio_estado_servicios,
                           name='administraciones-cambio-estado-servicios'
                       )

)



