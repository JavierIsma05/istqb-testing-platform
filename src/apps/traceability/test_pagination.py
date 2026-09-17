import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_matriz_pagina_cada_cinco_registros(client, user, requirement):
    for index in range(2, 13):
        requirement.__class__.objects.create(
            project=requirement.project,
            code=f'REQ-PAGE-{index:03d}',
            title=f'Requisito paginado {index}',
            description='Requisito creado para validar la paginación de la matriz.',
            created_by=user,
        )

    client.force_login(user)

    first_page = client.get(reverse('traceability:index'))
    second_page = client.get(reverse('traceability:index'), {'page': 2})
    third_page = client.get(reverse('traceability:index'), {'page': 3})

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert third_page.status_code == 200
    assert len(first_page.context['rows']) == 5
    assert len(second_page.context['rows']) == 5
    assert len(third_page.context['rows']) == 2
    assert first_page.context['matrix_page'].number == 1
    assert second_page.context['matrix_page'].number == 2
    assert third_page.context['matrix_page'].number == 3
    assert first_page.context['matrix_page'].paginator.per_page == 5
    assert first_page.context['matrix_page'].paginator.count == 12
    assert first_page.context['total_requirements'] == 12
    assert third_page.context['matrix_page'].has_previous
    assert not third_page.context['matrix_page'].has_next


@pytest.mark.django_db
def test_matriz_paginada_muestra_controles_solo_cuando_hay_mas_de_una_pagina(client, user, requirement):
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    content = response.content.decode()

    assert 'Paginación de la matriz de trazabilidad' not in content
