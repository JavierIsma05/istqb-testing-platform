from django.conf import settings
from django.db import models


class FormDraft(models.Model):
    # Borrador de formulario autoguardado, clave por usuario + modulo + registro.
    # object_id se representa en la clave compuesta; usar 0 para "registro nuevo".
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='form_drafts',
    )
    module = models.CharField(max_length=40)
    key = models.CharField(max_length=180)
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'key')

    def __str__(self):
        return f'{self.user_id} - {self.key}'
