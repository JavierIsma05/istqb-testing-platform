import datetime

from django import forms
from django.utils import timezone


def current_year_bounds():
    year = timezone.localdate().year
    return datetime.date(year, 1, 1), datetime.date(year, 12, 31)


def current_year_date_attrs(extra=None):
    min_date, max_date = current_year_bounds()
    attrs = {
        'min': min_date.isoformat(),
        'max': max_date.isoformat(),
    }
    if extra:
        attrs.update(extra)
    return attrs


class CurrentAcademicYearValidationMixin:
    """Rechaza cualquier valor de fecha fuera del año académico vigente.

    Se aplica a todos los DateField del formulario salvo que se indique
    lo contrario en ``current_year_fields``.
    """

    current_year_fields = None

    def clean(self):
        cleaned_data = super().clean()
        year = timezone.localdate().year
        fields = self.current_year_fields or [
            name
            for name, field in self.fields.items()
            if isinstance(field, forms.DateField)
        ]
        for name in fields:
            value = cleaned_data.get(name)
            if value and value.year != year:
                self.add_error(
                    name,
                    f'Solo se permiten fechas del año académico vigente ({year}).',
                )
        return cleaned_data
