# -*- coding: utf-8 -*-
from django.db import models

from ..core.models import TimeStampedModel, ModelStatus

from ..edificios.models import Edificios


class Contactos(TimeStampedModel, ModelStatus):
    """
    Contáctos de un edificio
    """
    edificio = models.ForeignKey(Edificios, verbose_name='Edificio')
    nombre = models.CharField(blank=False,
                              null=False,
                              verbose_name='Nombre completo',
                              max_length=150)
    piso = models.IntegerField(blank=True,
                               verbose_name='Piso donde vive',
                               max_length=2,
                               help_text='Piso del edificio, ejemplo: 1, 3, 5, 10')
    departamento = models.CharField(blank=True, max_length=2, help_text='Ej: A, B, D')
    telefono = models.CharField(max_length=50, blank=True)
    comentario = models.TextField(blank=True)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Contáctos'
        verbose_name_plural = 'Contáctos'


class HorariosContactos(TimeStampedModel):
    """
    Modelo para registrar el horario de
    los contactos del edificio
    """
    contacto = models.ForeignKey(Contactos)
    lunes = models.BooleanField(default=False, verbose_name='Lunes')
    martes = models.BooleanField(default=False, verbose_name='Martes')
    miercoles = models.BooleanField(default=False, verbose_name='Miércoles')
    jueves = models.BooleanField(default=False, verbose_name='Jueves')
    viernes = models.BooleanField(default=False, verbose_name='Viernes')
    sabado = models.BooleanField(default=False, verbose_name='Sábado')
    domingo = models.BooleanField(default=False, verbose_name='Domingo')
    hora_desde = models.TimeField(blank=False, null=False)
    hora_hasta = models.TimeField(blank=False, null=False)

    def __unicode__(self):
        return self.edificio.nombre

    class Meta:
        verbose_name = 'Horarios de contácto'
        verbose_name_plural = 'Horarios de contácto'
