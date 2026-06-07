from services.intent_service import IntentService


def test_detect_transferir_horario() -> None:
    service = IntentService()
    assert service.detect("Quero transferir meu horário") == "transferir_horario"


def test_detect_confirmar_transferencia_with_context() -> None:
    service = IntentService()
    assert service.detect("Opção 1", {"flow": "transferir_horario"}) == "confirmar_transferencia_horario"


def test_detect_trancar_matricula() -> None:
    service = IntentService()
    assert service.detect("Preciso trancar minha matrícula") == "trancar_matricula"


def test_detect_estagio() -> None:
    service = IntentService()
    assert service.detect("Tenho dúvidas sobre estágio obrigatório") == "orientacao_estagio"


def test_detect_notas() -> None:
    service = IntentService()
    assert service.detect("quero ver minhas notas") == "consultar_notas"


def test_detect_presencas() -> None:
    service = IntentService()
    assert service.detect("quantas faltas eu tenho?") == "consultar_presencas"
