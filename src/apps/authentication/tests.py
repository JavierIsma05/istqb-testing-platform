from django.urls import reverse


def test_pagina_de_login_responde_correctamente(client):
    response = client.get(reverse('login'))

    assert response.status_code == 200


def test_pagina_de_registro_responde_correctamente(client):
    response = client.get(reverse('register'))

    assert response.status_code == 200
