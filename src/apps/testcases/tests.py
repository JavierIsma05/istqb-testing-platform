import pytest
from django.urls import reverse

from apps.testcases.forms import TestCaseModalForm as CaseForm
from apps.testcases.models import TestCase as CaseModel


@pytest.mark.django_db
def test_caso_de_prueba_relaciona_plan_y_requisito(test_case, test_plan, requirement):
    assert test_case.test_plan == test_plan
    assert test_case.requirement == requirement
    assert test_case.status == CaseModel.Status.PENDING
    assert test_case.technique == CaseModel.Technique.BLACK_BOX
    assert str(test_case) == 'TC-001 - Login exitoso'


@pytest.mark.django_db
def test_formulario_de_caso_de_prueba_es_valido_con_pasos_y_resultado(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'code': 'TC-002',
            'title': 'Registro exitoso',
            'description': 'Validar registro de usuario',
            'priority': CaseModel.Priority.HIGH,
            'technique': CaseModel.Technique.EQUIVALENCE,
            'level': CaseModel.Level.SYSTEM,
            'preconditions': 'Usuario sin cuenta previa',
            'steps': 'Abrir registro => Se muestra el formulario\nCompletar datos => Los datos son aceptados\nEnviar => La cuenta se crea',
            'expected_result': 'La cuenta queda creada.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert form.is_valid()
    test_case = form.save(commit=False)
    assert len(test_case.steps_data) == 3


@pytest.mark.django_db
def test_estados_del_caso_siguen_soportando_flujo_istqb_con_nuevos_labels():
    assert CaseModel.Status.PENDING.label == 'En Redacción'
    assert CaseModel.Status.READY.label == 'Listo para Ejecutar'
    assert CaseModel.Status.RUNNING.label == 'Ejecutando'
    assert CaseModel.Status.PASSED.label == 'Completado'
    assert CaseModel.Status.FAILED.label == 'Fallido'


@pytest.mark.django_db
def test_formulario_de_caso_muestra_requisito_con_codigo_tipado(test_plan, requirement):
    form = CaseForm(user=test_plan.created_by, initial={'test_plan': test_plan.id})
    requirement.refresh_from_db()

    option = next(
        choice for choice in form.fields['requirement'].queryset
        if choice.pk == requirement.pk
    )
    assert form.fields['requirement'].label_from_instance(option) == f'{requirement.typed_code} - {requirement.title}'


@pytest.mark.django_db
def test_display_label_del_requisito_refleja_tipo_y_secuencia(requirement):
    assert requirement.type_prefix == 'RF'
    assert requirement.typed_code == 'RF-001'
    assert requirement.display_label == 'RF-001 - Autenticacion de usuarios'


@pytest.mark.django_db
def test_formulario_de_caso_acepta_pasos_numerados_sin_formato_accion_resultado(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'code': 'TC-003',
            'title': 'Login con pasos numerados',
            'description': 'Validar flujo con pasos numerados',
            'priority': CaseModel.Priority.HIGH,
            'technique': CaseModel.Technique.BLACK_BOX,
            'level': CaseModel.Level.SYSTEM,
            'preconditions': 'Usuario registrado',
            'steps': '1. Abrir login\n2. Ingresar credenciales\n3. Confirmar acceso',
            'expected_result': 'El usuario accede al dashboard.',
            'status': CaseModel.Status.READY,
        }
    )

    assert form.is_valid()
    assert len(form.save(commit=False).steps_data) == 3


@pytest.mark.django_db
def test_formulario_de_caso_exige_requisito_y_pasos_estructurados(test_plan):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': '',
            'title': 'Caso sin trazabilidad',
            'priority': CaseModel.Priority.MEDIUM,
            'technique': CaseModel.Technique.DECISION_TABLE,
            'level': CaseModel.Level.SYSTEM,
            'steps': '',
            'expected_result': 'No aplica.',
            'version': '1.0',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert not form.is_valid()
    assert 'requirement' in form.errors
    assert 'steps' in form.errors


@pytest.mark.django_db
def test_modal_carga_plan_y_requisitos_disponibles(client, project, requirement, test_plan, user):
    project.members.add(user)
    client.force_login(user)

    response = client.get(reverse('testcases:index'))
    form = response.context['form']

    assert response.status_code == 200
    assert form.fields['test_plan'].initial == test_plan.pk
    assert list(form.fields['requirement'].queryset) == [requirement]
    assert requirement.display_label in response.content.decode()


@pytest.mark.django_db
def test_formulario_de_caso_mantiene_el_valor_de_estado_del_plan_prueba_automatico(test_plan, requirement):
    form = CaseForm(user=test_plan.created_by)

    assert form.fields['test_plan'].widget.__class__.__name__ == 'HiddenInput'
    assert form.fields['test_plan'].initial == test_plan.pk


@pytest.mark.django_db
def test_formulario_acepta_tecnica_otra_con_tecnica_personalizada(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'title': 'Caso con tecnica propia',
            'description': 'Tecnica personalizada',
            'priority': CaseModel.Priority.MEDIUM,
            'technique': CaseModel.Technique.OTHER,
            'custom_technique': 'Inspeccion por pares',
            'preconditions': 'Ninguna',
            'steps': 'Revisar artefacto\nRegistrar hallazgos',
            'expected_result': 'Hallazgos documentados.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert form.is_valid(), form.errors
    test_case = form.save()
    assert test_case.technique == CaseModel.Technique.OTHER
    assert test_case.custom_technique == 'Inspeccion por pares'
    assert test_case.display_technique == 'Inspeccion por pares'


@pytest.mark.django_db
def test_formulario_exige_tecnica_personalizada_cuando_selecciona_otra(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'title': 'Caso sin tecnica escrita',
            'priority': CaseModel.Priority.MEDIUM,
            'technique': CaseModel.Technique.OTHER,
            'custom_technique': '',
            'steps': 'Paso uno',
            'expected_result': 'OK.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert not form.is_valid()
    assert 'custom_technique' in form.errors


@pytest.mark.django_db
def test_tecnica_existente_no_exige_tecnica_personalizada(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'title': 'Caso con tecnica estandar',
            'priority': CaseModel.Priority.MEDIUM,
            'technique': CaseModel.Technique.EQUIVALENCE,
            'steps': 'Paso uno',
            'expected_result': 'OK.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().custom_technique == ''
