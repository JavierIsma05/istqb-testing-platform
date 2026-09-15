from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.core.codes import next_code
from apps.incidents.models import Incident
from .models import TestPlan


def _normalized(value):
    return ' '.join(str(value or '').split()).strip().casefold()


def sync_risks_from_payload(plan, reported_by, payload):
    """Synchronize wizard risk data without deleting historical risk records.

    Existing risks are matched by their normalized title/description. Matching
    records are updated in place; new payload items create new risks. Existing
    records omitted from the payload are preserved so their historical
    evidence and relationships remain intact.
    """
    if not payload:
        return []

    existing = list(plan.risks.all().order_by('pk'))
    used_ids = set()
    affected = []

    for raw in payload:
        if not isinstance(raw, dict):
            continue
        title = (raw.get('title') or '').strip()
        description = (raw.get('description') or '').strip()
        mitigation = (raw.get('mitigation_strategy') or '').strip()
        probability = raw.get('probability') or Incident.Probability.MEDIUM
        impact = raw.get('impact') or Incident.Impact.MEDIUM
        if not description and not mitigation:
            continue
        title = title or description[:80] or 'Riesgo del plan'

        match = next(
            (
                risk for risk in existing
                if risk.pk not in used_ids
                and _normalized(risk.title) == _normalized(title)
                and _normalized(risk.description) == _normalized(description)
            ),
            None,
        )
        if match:
            match.title = title[:180]
            match.description = description
            match.mitigation_strategy = mitigation
            match.probability = probability if probability in dict(Incident.Probability.choices) else Incident.Probability.MEDIUM
            match.impact = impact if impact in dict(Incident.Impact.choices) else Incident.Impact.MEDIUM
            match.save(update_fields=['title', 'description', 'mitigation_strategy', 'probability', 'impact'])
            used_ids.add(match.pk)
            affected.append(match)
            continue

        incident = Incident(
            project=plan.project,
            test_plan=plan,
            code=next_code(Incident.objects.filter(project=plan.project), 'INC'),
            title=title,
            description=description,
            mitigation_strategy=mitigation,
            probability=probability if probability in dict(Incident.Probability.choices) else Incident.Probability.MEDIUM,
            impact=impact if impact in dict(Incident.Impact.choices) else Incident.Impact.MEDIUM,
            reported_by=reported_by,
        )
        incident.save()
        affected.append(incident)

    return affected


def create_risks_from_payload(plan, reported_by, payload):
    """Backward-compatible alias used by the creation workflow."""
    return sync_risks_from_payload(plan, reported_by, payload)


class WizardRiskForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ('title', 'description', 'mitigation_strategy', 'probability', 'impact')
        labels = {
            'title': 'Titulo del riesgo',
            'description': 'Descripcion',
            'mitigation_strategy': 'Mitigacion / respuesta',
            'probability': 'Probabilidad',
            'impact': 'Impacto',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Riesgo de integracion con API externa'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe el riesgo, causa probable y efecto esperado', 'rows': 2}),
            'mitigation_strategy': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Indica como se evitara, reducira, transferira o aceptara el riesgo', 'rows': 2}),
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
