"""Un enlace de Moodle a YouTube o Vimeo se sincroniza como «video»."""

import pytest

from src.infrastructure.adapters.out_.moodle_api_adapter import tipo_actividad


def _url(destino: str) -> dict:
    return {"modname": "url", "contents": [{"type": "url", "fileurl": destino}]}


@pytest.mark.parametrize(
    "destino",
    [
        "https://www.youtube.com/watch?v=abc123",
        "https://youtu.be/abc123",
        "https://m.youtube.com/watch?v=abc123",
        "https://vimeo.com/123456",
    ],
)
def test_enlace_a_video_es_video(destino):
    assert tipo_actividad(_url(destino)) == "video"


@pytest.mark.parametrize(
    "destino",
    [
        "https://www.geogebra.org/calculator",
        "https://es.khanacademy.org/math/statistics-probability",
        "https://notyoutube.com/watch?v=abc",
        "",
    ],
)
def test_otro_enlace_sigue_siendo_url(destino):
    assert tipo_actividad(_url(destino)) == "url"


def test_enlace_sin_contenidos_sigue_siendo_url():
    assert tipo_actividad({"modname": "url"}) == "url"


@pytest.mark.parametrize("modulo", ["quiz", "page", "assign", "forum"])
def test_otros_modulos_no_cambian(modulo):
    assert (
        tipo_actividad(
            {"modname": modulo, "contents": [{"fileurl": "https://youtu.be/x"}]}
        )
        == modulo
    )
