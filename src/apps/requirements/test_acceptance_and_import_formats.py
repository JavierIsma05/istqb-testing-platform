import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.requirements.forms import RequirementImportForm, RequirementForm
from apps.requirements.models import Requirement
from apps.requirements.services import extract_text_from_source, parse_requirements_from_text


@pytest.mark.django_db
def test_requisito_acepta_criterios_de_aceptacion(project):
    form = RequirementForm(
        data={
            'project': project.pk,
            'title': 'Recuperar contraseña',
            'description': 'El sistema permite recuperar la contraseña.',
            'acceptance_criteria': 'Debe solicitar un correo válido.\nEl enlace debe expirar en 30 minutos.',
            'requirement_type': Requirement.RequirementType.FUNCTIONAL,
            'priority': Requirement.Priority.HIGH,
        },
    )
    assert form.is_valid(), form.errors
    assert 'criterios' in form.fields['acceptance_criteria'].label.lower()


@pytest.mark.django_db
def test_importador_acepta_csv_y_txt(project):
    csv_file = SimpleUploadedFile(
        'requirements.csv',
        b'Codigo,Titulo,Descripcion\nREQ-001,Login,El sistema debe permitir iniciar sesion.\n',
        content_type='text/csv',
    )
    form = RequirementImportForm(
        data={'project': project.pk},
        files={'source_file': csv_file},
        projects=project.__class__.objects.filter(pk=project.pk),
    )
    assert form.is_valid()
    text = extract_text_from_source(form.cleaned_data['source_file'])
    assert 'REQ-001' in text


@pytest.mark.django_db
def test_importador_rechaza_extension_no_documental(project):
    executable = SimpleUploadedFile('script.exe', b'not allowed', content_type='application/octet-stream')
    form = RequirementImportForm(
        data={'project': project.pk},
        files={'source_file': executable},
        projects=project.__class__.objects.filter(pk=project.pk),
    )
    assert not form.is_valid()
    assert 'source_file' in form.errors


def test_parser_conserva_requisitos_importados_desde_filas():
    text = 'REQ-001 | Login | El sistema debe permitir iniciar sesion.\nREQ-002 | Seguridad | El sistema debe cifrar las credenciales.'
    items = parse_requirements_from_text(text)
    assert len(items) == 2
    assert items[0].description
