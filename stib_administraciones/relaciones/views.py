# -*- coding: utf-8 -*-
import json
from itertools import chain
from operator import attrgetter
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import FormView, CreateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin

from .forms import (FormDefinirTipoComunicacion,
                    FormNotificacionUsuariosProductos,
                    FormNotificacionUsuariosServicios,
                    FormNotificacionEdificiosProductos,
                    FormNotificacionEdificiosServicios,
                    FormNotificacionesEdificiosSearch,
                    FormNotificacionesAdministracionesSearch)
from .models import (RelacionesUsuariosProductos,
                     RelacionesUsuariosServicios,
                     RelacionesEdificiosProductos,
                     RelacionesEdificiosServicios)
from ..productos.models import Productos
from ..servicios.models import Servicios
from ..edificios.models import Edificios
from ..perfiles.models import Perfiles
from ..settings_local import STIB_TO_EMAIL


reenvio_email_massages = {'success': 'Se ha reenviado el mail de notificación.',
                          'error': 'Error al enviar el mail de notificación.'}


class EstablecerTipoComunicacion(LoginRequiredMixin, StaffuserRequiredMixin, FormView):
    """
    Vista que presentara un formulario
    para definir el tipo de comunicacion
    """
    template_name = 'relaciones/establecer_tipo_comunicacion.html'
    form_class = FormDefinirTipoComunicacion
    raise_exception = True

    def form_valid(self, form):
        """
        Armamos la Url encargada de redirigir a la pantalla
        adecuada para enviar la notificacion
        """
        entidad = form.cleaned_data["entidad"]
        destinatario = form.cleaned_data["destinatario"]
        self.success_url = entidad + "-" + destinatario
        return super(EstablecerTipoComunicacion, self).form_valid(form)


class NotificarCreateViewMixin(LoginRequiredMixin, StaffuserRequiredMixin, CreateView):
    template_name = 'relaciones/notificar_form.html'
    raise_exception = True

    def get_success_url(self):
        # -- enviar por mail, solo si desde
        # -- el formulario se indica que se quieren enviar por email...
        if self.object.enviado:
            if self._enviar_aviso_por_email(self.object):
                self.model.marcar_email_recibido(self.object.pk)
        messages.success(self.request, 'La notificación se envió con éxito.')
        return reverse('notificaciones:definir')

    def _enviar_aviso_por_email(self, obj):
        try:
            # -- obtengo Id de usuario
            if hasattr(obj, 'edificio') is False:
                user = obj.usuario.id
                tmp_subject = 'Aviso importante'
            else:
                user = Edificios.usuario_por_edificio(obj.edificio.id)
                tmp_subject = str(obj.edificio)

            # -- obtengo direccion de mail
            email = Perfiles.obtener_mail_por_usuario(user)

            # -- tiene email cargado?
            if len(email) > 0:
                subject = "[STIB] [%s] %s" % (obj.tipo_relacion, tmp_subject)
                ctx = {'link_vista': self.request.build_absolute_uri(_get_url_view(obj))}
                body = render_to_string("emails/email_notificaciones.html", ctx)
                return _send_email(email, subject, body)
            else:
                return False
        except:
            return False


class NotificarProductosUsuarios(NotificarCreateViewMixin):
    """
    Notificar a usuarios(administraciones) sobre determinados
    productos
    """
    model = RelacionesUsuariosProductos
    form_class = FormNotificacionUsuariosProductos

    def get_context_data(self, **kwargs):
        ctx = super(NotificarProductosUsuarios, self).get_context_data(**kwargs)
        ctx['page_title'] = 'Notificaciones de Productos para Administraciones'
        return ctx


class NotificarServiciosUsuarios(NotificarCreateViewMixin):
    """
    Notificar a usuarios(administraciones) sobre determinados
    servicios.
    """
    model = RelacionesUsuariosServicios
    form_class = FormNotificacionUsuariosServicios

    def get_context_data(self, **kwargs):
        ctx = super(NotificarServiciosUsuarios, self).get_context_data(**kwargs)
        ctx['page_title'] = 'Notificaciones de Servicios para Administraciones'
        return ctx


class NotificarProductosEdificios(NotificarCreateViewMixin):
    """ Notificar a edificio sobre determinados productos. """
    model = RelacionesEdificiosProductos
    form_class = FormNotificacionEdificiosProductos

    def get_context_data(self, **kwargs):
        ctx = super(NotificarProductosEdificios, self).get_context_data(**kwargs)
        ctx['page_title'] = 'Notificaciones de Productos para Edificios'
        return ctx


class NotificarServiciosEdificios(NotificarCreateViewMixin):
    """ Notificar a edificio sobre determinados servicios. """
    model = RelacionesEdificiosServicios
    form_class = FormNotificacionEdificiosServicios

    def get_context_data(self, **kwargs):
        ctx = super(NotificarServiciosEdificios, self).get_context_data(**kwargs)
        ctx['page_title'] = 'Notificaciones de Servicios para Edificios'
        return ctx


@staff_member_required
def get_autocomplete_result(request):
    """
    Busqueda de productos y servicios, se utiliza en una llamada
    ajax en el formulario para auto-sugerir el resultado.
    """
    # -- término a buscar --
    q = request.GET['term']
    # -- parametro que indica en que modelo bsucar --
    obj = request.GET['obj']
    # -- convierto string a isntancia de clase --
    class_instance = globals()[obj]
    # -- consulta sql para obtener el resultado --
    results = class_instance.objects.filter(nombre__icontains=q)
    results_list = []

    for result in results:
        dic_result = {}
        dic_result['id'] = result.id
        dic_result['label'] = result.nombre
        results_list.append(dic_result)

    return HttpResponse(json.dumps(results_list), mimetype="application/json")


@staff_member_required
def get_autocomplete_edificios_result(request):
    """
    Busqueda de edificios, se utiliza en una llamada
    ajax en el formulario para auto-sugerir el resultado.
    """
    # -- término a buscar --
    q = request.GET['term']
    # -- busqueda por nombre o direccion de edificio
    edificios = Edificios.objects.filter(Q(nombre__icontains=q) | Q(direccion__icontains=q))

    results_list = []

    for edificio in edificios:
        dic_result = {}
        dic_result['id'] = edificio.id
        dic_result['label'] = edificio.nombre + " - " + edificio.direccion
        results_list.append(dic_result)

    return HttpResponse(json.dumps(results_list), mimetype="application/json")


def _get_queries_results(queries):
    """
    iteramos las queries, usamos el método from_iterable
    del objecto chain porque le pasamos una tupla de queries
    """
    return sorted(
        chain.from_iterable(queries),
        key=attrgetter('creado'),
        reverse=True
    )


def _get_filter_results(request, query_prod_base, query_serv_base):
    """
    Filtros para los listados de notificaciones
    de productos y servicios
    """
    q_prod = query_prod_base  # query base de productos
    q_servicios = query_serv_base  # query base de servicios

    # -- sobre que entidades queremos realizar la busqueda?
    entidades = request.POST.get('entidades', 0)
    if entidades == "1":  # -- productos?
        q_servicios = False  # -- exluyo la busqueda sobre servicios
    elif entidades == "2":  # -- servicios?
        q_prod = False  # -- exluyo la busqueda sobre productos

    # -- titulo?
    titulo = request.POST['titulo']
    if titulo:
        if q_prod is not False:
            q_prod = q_prod.filter(titulo__icontains=titulo)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(titulo__icontains=titulo)

    # -- descripcion?
    descripcion = request.POST['descripcion']
    if descripcion:
        if q_prod is not False:
            q_prod = q_prod.filter(descripcion__icontains=descripcion)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(descripcion__icontains=descripcion)

    # -- leido?
    leido = request.POST['leido']
    if leido:
        if q_prod is not False:
            q_prod = q_prod.filter(leido=True if leido == 1 else False)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(leido=True if leido == "1" else False)

    # -- mail enviado?
    mail = request.POST['mail']
    if mail:
        if q_prod is not False:
            q_prod = q_prod.filter(enviado=True if mail == 1 else False)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(enviado=True if mail == "1" else False)

    # -- mail recibido?
    mail_recibido_value = request.POST['mail_recibido']
    if mail_recibido_value:
        if q_prod is not False:
            q_prod = q_prod.filter(mail_recibido=True if mail_recibido_value == "1" else False)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(mail_recibido=True if mail_recibido_value == "1" else False)

    # -- motivos?
    motivo = request.POST['motivos']
    if motivo:
        if q_prod is not False:
            q_prod = q_prod.filter(tipo_relacion=motivo)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(tipo_relacion=motivo)

    # -- producto?
    producto = request.POST['producto']
    if producto:
        if q_prod is not False:
            q_prod = q_prod.filter(producto=producto)

    # -- servicio?
    servicio = request.POST['servicio']
    if servicio:
        if q_servicios is not False:
            q_servicios = q_servicios.filter(servicio=servicio)

    # -- edificio?
    edificio = request.POST.get('edificio', False)
    if edificio:
        if q_prod is not False:
            q_prod = q_prod.filter(edificio=edificio)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(edificio=edificio)

    # -- fechas desde/hasta
    fecha_desde = request.POST['fecha_desde']
    fecha_hasta = request.POST['fecha_hasta']
    if fecha_desde and fecha_hasta:
        fecha_desde = fecha_desde.split('/')
        fecha_hasta = fecha_hasta.split('/')
        fecha_desde = fecha_desde[2] + "-" + fecha_desde[1] + "-" + fecha_desde[0]
        fecha_hasta = fecha_hasta[2] + "-" + fecha_hasta[1] + "-" + fecha_hasta[0]
        if q_prod is not False:
            q_prod = q_prod.filter(creado__gte=fecha_desde, creado__lte=fecha_hasta)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(creado__gte=fecha_desde, creado__lte=fecha_hasta)

    # -- usuarios?
    usuario = request.POST.get('usuario', False)
    if usuario:
        # -- si estamos filtrando notificaciones de edificios
        # -- realizamos la busqueda de usuario a traves del edificio
        # -- antes debemos asegurarno de que la query no sea false
        if isinstance("" if q_prod is False else q_prod[0], RelacionesEdificiosProductos) or \
                isinstance("" if q_servicios is False else q_servicios[0], RelacionesEdificiosServicios):
            if q_prod is not False:
                q_prod = q_prod.filter(edificio__user=usuario)
            if q_servicios is not False:
                q_servicios = q_servicios.filter(edificio__user=usuario)
        else:
            if q_prod is not False:
                q_prod = q_prod.filter(usuario=usuario)
            if q_servicios is not False:
                q_servicios = q_servicios.filter(usuario=usuario)

    # -- estado?
    estado = request.POST.get('estado', False)
    if estado:
        if q_prod is not False:
            q_prod = q_prod.filter(estado=estado)
        if q_servicios is not False:
            q_servicios = q_servicios.filter(estado=estado)

    # -- no se puede devolver un boolean,
    # -- si es boolean, devolvemos un string vacio
    return ["" if q_prod is False else q_prod,
            "" if q_servicios is False else q_servicios]


@staff_member_required
def listar_notificaciones_edificios(request):
    """
    Listar las notificaciones de los Edificios, combinamos
    los productos y servicios...
    """
    queries = [RelacionesEdificiosProductos.objects.all(), RelacionesEdificiosServicios.objects.all()]
    ctx = {
        'search_form': FormNotificacionesEdificiosSearch,
        'collapse_filters': False
    }

    if request.method == "POST":
        search_form = FormNotificacionesEdificiosSearch(request.POST)
        if search_form.is_valid():
            queries = _get_filter_results(request, queries[0], queries[1])
        else:
            ctx['search_form'] = search_form
            ctx['collapse_filters'] = True

    ctx['results'] = _get_queries_results(queries)

    return render(request, 'relaciones/notificaciones_edificios_list.html', ctx)


@staff_member_required
def listar_notificaciones_admnistraciones(request):
    """
    Listar las notificaciones de las administraciones, combinamos
    los productos y servicios...
    """
    queries = [RelacionesUsuariosProductos.objects.all(), RelacionesUsuariosServicios.objects.all()]

    ctx = {'search_form': FormNotificacionesAdministracionesSearch,
           'collapse_filters': False}

    if request.method == 'POST':
        search_form = FormNotificacionesAdministracionesSearch(request.POST)
        if search_form.is_valid():
            queries = _get_filter_results(request, queries[0], queries[1])
        else:
            ctx['search_form'] = search_form
            ctx['collapse_filters'] = True

    ctx['results'] = _get_queries_results(queries)

    return render(request, 'relaciones/notificaciones_administraciones_list.html', ctx)


class NotificacionesDeleteViewMixin(object):
    """ Mixin para el Delete de las Notificaciones """
    template_name = 'relaciones/notificaciones_confirm_delete.html'

    success_url = None

    def get_success_url(self):
        messages.success(self.request, 'La notificación fue eliminada.')
        return self.success_url


class NotificacionesEdificiosProductosDeleteView(LoginRequiredMixin, StaffuserRequiredMixin,
                                                 NotificacionesDeleteViewMixin, DeleteView):
    """ Eliminar notificaciones para edificios de productos """
    model = RelacionesEdificiosProductos
    success_url = reverse_lazy('notificaciones:edificios-list')
    raise_exception = True


class NotificacionesEdificiosServiciosDeleteView(LoginRequiredMixin, StaffuserRequiredMixin,
                                                 NotificacionesDeleteViewMixin, DeleteView):
    """ Eliminar notificaciones para edificios de servicios """
    model = RelacionesEdificiosServicios
    success_url = reverse_lazy('notificaciones:edificios-list')
    raise_exception = True


class NotificacionesAdministracionesProductosDeleteView(LoginRequiredMixin, StaffuserRequiredMixin,
                                                        NotificacionesDeleteViewMixin, DeleteView):
    """ Eliminar notificaciones de productos para administraciones """
    model = RelacionesUsuariosProductos
    success_url = reverse_lazy('notificaciones:administraciones-list')
    raise_exception = True


class NotificacionesAdministracionesServiciosDeleteView(LoginRequiredMixin, StaffuserRequiredMixin,
                                                        NotificacionesDeleteViewMixin, DeleteView):
    """ Eliminar notificaciones de servicios para administraciones """
    model = RelacionesUsuariosServicios
    success_url = reverse_lazy('notificaciones:administraciones-list')
    raise_exception = True


@staff_member_required
def reenviar_email_edificios_productos(request, notificacion):
    """
    - reenvío de email para avisar de una nueva notificación de productos
    para un Edificio
    """
    if request.method == 'GET':
        notificacion = RelacionesEdificiosProductos.objects.get(pk=notificacion)
        if _reenviar_email_notificaciones(request, notificacion):
            messages.success(request, reenvio_email_massages['success'])
        else:
            messages.error(request, reenvio_email_massages['error'])

    return HttpResponseRedirect(reverse("notificaciones:edificios-list"))


@staff_member_required
def reenviar_email_edificios_servicios(request, notificacion):
    """
    - reenvío de email para avisar de una nueva notificación de servicios
    para un Edificio
    """
    if request.method == 'GET':
        notificacion = RelacionesEdificiosServicios.objects.get(pk=notificacion)
        if _reenviar_email_notificaciones(request, notificacion):
            messages.success(request, reenvio_email_massages['success'])
        else:
            messages.error(request, reenvio_email_massages['error'])

    return HttpResponseRedirect(reverse("notificaciones:edificios-list"))


@staff_member_required
def reenviar_email_administraciones_productos(request, notificacion):
    """
    reenvio de email para avisar de una nueva notificación de productos
    para una 'Administracion'
    """
    if request.method == 'GET':
        notificacion = RelacionesUsuariosProductos.objects.get(pk=notificacion)
        if _reenviar_email_notificaciones(request, notificacion):
            messages.success(request, reenvio_email_massages['success'])
        else:
            messages.error(request, reenvio_email_massages['error'])

    return HttpResponseRedirect(reverse("notificaciones:administraciones-list"))


@staff_member_required
def reenviar_email_administraciones_servicios(request, notificacion):
    """
    reenvio de email para avisar de una nueva notificación de servicios
    para una 'Administracion'
    """
    if request.method == 'GET':
        notificacion = RelacionesUsuariosServicios.objects.get(pk=notificacion)
        if _reenviar_email_notificaciones(request, notificacion):
            messages.success(request, reenvio_email_massages['success'])
        else:
            messages.error(request, reenvio_email_massages['error'])

    return HttpResponseRedirect(reverse("notificaciones:administraciones-list"))


def _reenviar_email_notificaciones(request, obj_notificacion):
    """
    * Funciona que maneja en reenvio de emails.
    * obj_notificacion : es un objeto del tipo
        RelacionesEdificiosProductos, RelacionesEdificiosServicios,
        RelacionesUsuariosSProductos o RelacionesUsuariosServicios
    """
    # -- subject dependiendo el Tipo de Notificacion (Novedades/Servicios)
    subject = "[STIB] - [%s] " % obj_notificacion.tipo_relacion.nombre

    if isinstance(obj_notificacion, RelacionesEdificiosServicios) or \
            isinstance(obj_notificacion, RelacionesEdificiosProductos):
        # -- obtenemos el usuario del edificio del que queremos
        # -- enviar la notificaciones
        user = Edificios.usuario_por_edificio(obj_notificacion.edificio.id)
        subject += obj_notificacion.edificio.nombre + " - " + obj_notificacion.edificio.direccion
    else:
        user = obj_notificacion.usuario.id
        subject += ' Aviso Importante'

    # -- obtenemos el email al que enviaremos el recordatorio
    email_to = Perfiles.obtener_mail_por_usuario(user)

    ctx = {'link_vista': request.build_absolute_uri(_get_url_view(obj_notificacion))}
    body = render_to_string("emails/email_notificaciones.html", ctx)
    # -- mail enviado??
    if _send_email(email_to, subject, body):
        # -- marcamos como email recibido
        obj_notificacion.mail_recibido = True
        obj_notificacion.enviado = True
        obj_notificacion.save()
        return True
    else:
        return False


def _send_email(email_to, subject, body, *args):
    """
    Envío de email
    """
    try:
        if isinstance(email_to, tuple) is False:
            email_to = (email_to, )

        msg = EmailMessage(subject=subject,
                           body=body,
                           from_email='no-reply@stibadministraciones.com',
                           to=email_to)
        msg.content_subtype = 'html'
        msg.send()
        return True
    except:
        return False


class NotificacionesEdificiosServiciosDetailView(LoginRequiredMixin, DetailView):
    """
    Mostrar el detalle de una notificacion de servicio
    para un Edificio
    """
    model = RelacionesEdificiosServicios
    template_name = 'relaciones/notificaciones_edificios_detail.html'

    def get_queryset(self):
        qs = RelacionesEdificiosServicios.objects.filter(pk=self.kwargs['pk'])
        # -- debemos ademas estar seguros que la notificacion
        # -- sea de la administracion logueada
        qs.filter(edificio__user=self.request.user.id)

        # -- si no esta leido, se marca como leida
        if qs[0].leido is False:
            RelacionesEdificiosServicios.marcar_leido(qs[0].id)

        return qs


class NotificacionesEdificiosProductosDetailView(LoginRequiredMixin, DetailView):
    """
    Mostrar el detalle de una notificacion de producto
    para un Edificio
    """
    model = RelacionesEdificiosProductos
    template_name = 'relaciones/notificaciones_edificios_detail.html'

    def get_queryset(self):
        qs = RelacionesEdificiosProductos.objects.filter(pk=self.kwargs['pk'])
        # -- debemos ademas estar seguros que la notificacion
        # -- sea de la administracion logueada
        qs.filter(edificio__user=self.request.user.id)

        # -- si no esta leido, se marca como leida
        if qs[0].leido is False:
            RelacionesEdificiosProductos.marcar_leido(qs[0].id)

        return qs


@login_required(redirect_field_name='accounts/login/')
def edificios_cambio_estado_productos(request):
    if request.method == "POST" and request.POST.get("id"):
        try:
            RelacionesEdificiosProductos.cambiar_estado(request.POST.get("id"),
                                                        request.POST.get("estado"))

            _send_email_cambio_estado(request, RelacionesEdificiosProductos)

            messages.success(request, "Se ha cambiado el estado de la Notificación")
        except:
            messages.error(request, "Error al cambiar el estado de la Notificación")

        return HttpResponseRedirect(reverse('notificaciones:edificios-productos-detail',
                                    args=[request.POST.get("id")]))
    else:
        messages.success(request, "Error.")
        return HttpResponseRedirect("/")


@login_required(redirect_field_name='accounts/login/')
def edificios_cambio_estado_servicios(request):
    if request.method == "POST" and request.POST.get("id"):
        try:
            RelacionesEdificiosServicios.cambiar_estado(request.POST.get("id"),
                                                        request.POST.get("estado"))

            _send_email_cambio_estado(request, RelacionesEdificiosServicios)

            messages.success(request, "Se ha cambiado el estado de la Notificación")
        except:
            messages.error(request, "Error al cambiar el estado de la Notificación")

        return HttpResponseRedirect(reverse('notificaciones:edificios-servicios-detail',
                                            args=[request.POST.get("id")]))
    else:
        messages.success(request, "Error.")
        return HttpResponseRedirect("/")


class NotificacionesAdministracionesProductosDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle de notificacion de Productos de
    una administracion determinada
    """
    model = RelacionesUsuariosProductos
    template_name = 'relaciones/notificaciones_administraciones_detail.html'

    def get_queryset(self):
        qs = RelacionesUsuariosProductos.objects.filter(pk=self.kwargs['pk'])
        # -- debemos ademas estar seguros que la notificacion
        # -- sea de la administracion logueada
        qs.filter(usuario=self.request.user.id)

        # -- si no esta leido, se marca como leida
        if qs[0].leido is False:
            RelacionesUsuariosProductos.marcar_leido(qs[0].id)

        return qs


class NotificacionesAdministracionesServiciosDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle de notificacion de Servicio de
    una administracion determinada
    """
    model = RelacionesUsuariosServicios
    template_name = 'relaciones/notificaciones_administraciones_detail.html'

    def get_queryset(self):
        qs = RelacionesUsuariosServicios.objects.filter(pk=self.kwargs['pk'])
        # -- debemos ademas estar seguros que la notificacion
        # -- sea de la administracion logueada
        qs.filter(usuario=self.request.user.id)

        # -- si no esta leido, se marca como leida
        if qs[0].leido is False:
            RelacionesUsuariosServicios.marcar_leido(qs[0].id)

        return qs


@login_required(redirect_field_name='accounts/login/')
def administraciones_cambio_estado_productos(request):
    if request.method == "POST" and request.POST.get("id"):
        try:
            RelacionesUsuariosProductos.cambiar_estado(request.POST.get("id"),
                                                        request.POST.get("estado"))

            _send_email_cambio_estado(request, RelacionesUsuariosProductos)

            messages.success(request, "Se ha cambiado el estado de la Notificación")
        except:
            messages.error(request, "Error al cambiar el estado de la Notificación")

        return HttpResponseRedirect(reverse('notificaciones:administraciones-productos-detail',
                                            args=[request.POST.get("id")]))
    else:
        messages.success(request, "Error.")
        return HttpResponseRedirect("/")


@login_required(redirect_field_name='accounts/login/')
def administraciones_cambio_estado_servicios(request):
    if request.method == "POST" and request.POST.get("id"):
        try:
            RelacionesUsuariosServicios.cambiar_estado(request.POST.get("id"),
                                                        request.POST.get("estado"))

            _send_email_cambio_estado(request, RelacionesUsuariosServicios)

            messages.success(request, "Se ha cambiado el estado de la Notificación")
        except:
            messages.error(request, "Error al cambiar el estado de la Notificación")

        return HttpResponseRedirect(reverse('notificaciones:administraciones-productos-detail',
                                            args=[request.POST.get("id")]))
    else:
        messages.success(request, "Error.")
        return HttpResponseRedirect("/")


def _send_email_cambio_estado(request, model_obj):
    """
    Se arma el contenido y subjecto del email anunciando
    el cambio de estado de una determinada notificacion.
    Una vez lista la información se envía el mail.
    """
    notificacion = get_object_or_404(model_obj, pk=request.POST.get("id"))

    ctx = {
        'estado': model_obj.ESTADOS[ int(request.POST.get("estado"))-1 ][1],
        'descripcion': notificacion.descripcion,
        'fecha': notificacion.creado,
        'comentario': request.POST.get("comentario")
    }

    # -- si se trata de un servicio
    if hasattr(notificacion, 'servicio'):
        ctx['servicio'] = notificacion.servicio
    else:
        ctx['producto'] = notificacion.producto

    # -- si se trata de una notificacion de un edificio
    # -- o de una adminsitracion
    if hasattr(notificacion, 'edificio'):
        ctx['edificio'] = notificacion.edificio
        ctx['administracion'] = notificacion.edificio.user.perfil.nombre_comercial
        subject = "Edificio: %s - Notificación de Producto - Cambio de estado" % notificacion.edificio
    else:
        ctx['administracion'] = notificacion.usuario.perfil.nombre_comercial
        subject = u"Administración: %s - Notificación de Producto - Cambio de estado" % notificacion.usuario.perfil.nombre_comercial

    body = render_to_string('emails/email_cambio_estado_nota_tecnica_notificaciones.html', ctx)

    _send_email(STIB_TO_EMAIL, subject, body)


@login_required
def notificiones_edificio(request, edificio):
    """
    Listado de las notificaciones de productos o servicios
    de un edificio en particular...
    """
    if request.method == 'GET':
        ctx = {
            'notificaciones_productos': RelacionesEdificiosProductos.objects.filter(edificio=edificio),
            'notificaciones_servicios': RelacionesEdificiosServicios.objects.filter(edificio=edificio),
            'edificio': Edificios.objects.values("id", "nombre").get(pk=edificio)
        }
        return render(request, 'relaciones/notificaciones_edificio.html', ctx)
    else:
        return HttpResponseRedirect(reverse("edificios:administraciones"), args=[edificio])


class NotificacionesAdministracionListView(LoginRequiredMixin, TemplateView):
    """
    Listado de notificaciones de productos y/o servicios
    para una administracion determinada.
    """
    template_name = 'relaciones/notificaciones_administracion.html'

    def get_context_data(self, **kwargs):
        ctx = super(NotificacionesAdministracionListView, self).get_context_data(**kwargs)
        ctx['notificaciones_productos'] = RelacionesUsuariosProductos.objects.filter(usuario=self.request.user.id)
        ctx['notificaciones_servicios'] = RelacionesUsuariosServicios.objects.filter(usuario=self.request.user.id)

        return ctx


def _get_url_view(obj):
    """
    Dependiendo si es una notificacion de una administracion o de un edificio, si
    se trata de un servicio o producto, armamos el link para que desde el mail
    visiten la notificacion...
    """
    if hasattr(obj, 'edificio'):
        if hasattr(obj, 'producto'):
            return reverse('notificaciones:edificios-productos-detail', args=[obj.id])
        else:
            return reverse('notificaciones:edificios-servicios-detail', args=[obj.id])
    else:
        if hasattr(obj, 'producto'):
            return reverse('notificaciones:administraciones-productos-detail', args=[obj.id])
        else:
            return reverse('notificaciones:administraciones-servicios-detail', args=[obj.id])

