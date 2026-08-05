from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.core.codes import next_code
from apps.incidents.models import Incident
from .models import TestPlan


def create_risks_from_payload(plan, reported_by, payload):
    """Crea los Incident (riesgos) del plan a partir de la lista enviada por el
    asistente (campo oculto `risks_json`). Cada item debe ser un dict con las
    claves: title, description, mitigation_strategy, probability, impact."""
    if not payload:
        return []
    created = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        title = (raw.get('title') or '').strip()
        description = (raw.get('description') or '').strip()
        mitigation = (raw.get('mitigation_strategy') or '').strip()
        probability = raw.get('probability')
        impact = raw.get('impact')
        if not description and not mitigation:
            continue
        incident = Incident(
            project=plan.project,
            test_plan=plan,
            code=next_code(Incident.objects.filter(project=plan.project), 'INC'),
            title=title or description[:80] or 'Riesgo del plan',
            description=description,
            mitigation_strategy=mitigation,
            probability=probability or Incident.Probability.MEDIUM,
            impact=impact or Incident.Impact.MEDIUM,
            reported_by=reported_by,
        )
        incident.save()
        created.append(incident)
    return created


class WizardRiskForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = (
            'title',
            'description',
            'mitigation_strategy',
            'probability',
            'impact',
        )
        labels = {
            'title': 'Titulo del riesgo',
            'description': 'Descripcion',
            'mitigation_strategy': 'Mitigacion / respuesta',
            'probability': 'Probabilidad',
            'impact': 'Impacto',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Riesgo de integracion con API externa'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el riesgo, causa probable y efecto esperado',
                    'rows': 2,
                }
            ),
            'mitigation_strategy': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Indica como se evitara, reducira, transferira o aceptara el riesgo',
                    'rows': 2,
                }
            ),
            'probability': forms.Select(attrs={'class': 'form-select'}),
            'impact': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['description'].required = True
        self.fields['mitigation_strategy'].required = True
        self.fields['code'] = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get('title') or '').strip():
            description = (cleaned_data.get('description') or '').strip()
            cleaned_data['title'] = description[:80] or 'Riesgo del plan'
        return cleaned_data


class BaseWizardRiskFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs.pop('form_kwargs', None)
        super().__init__(*args, form_kwargs={}, **kwargs)

    def save_new(self, form, commit=True):
        obj = form.save(commit=False)
        if self.instance.pk is None:
            self.instance.save()
        obj.project = self.instance.project
        obj.test_plan = self.instance
        obj.code = next_code(Incident.objects.filter(project=obj.project), 'INC')
        obj.reported_by = getattr(self, 'reported_by', None)
        if commit:
            obj.save()
        return obj


WizardRiskFormSet = inlineformset_factory(
    TestPlan,
    Incident,
    form=WizardRiskForm,
    formset=BaseWizardRiskFormSet,
    extra=1,
    can_delete=False,
)