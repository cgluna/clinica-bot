"""
Script: cria um evento PENDENTE no Google Agenda quando o paciente escolhe um horário,
e dispara um e-mail informativo pra clínica avisando da nova solicitação.

Fluxo simulado neste teste (depois isso vai ser chamado pelo bot do WhatsApp):
1. Lista os horários disponíveis (reaproveita a lógica de check_availability.py)
2. Simula a escolha do paciente (input manual, por enquanto)
3. Revalida que o horário ainda está livre (evita conflito de 2 pessoas escolhendo ao mesmo tempo)
4. Cria o evento na agenda com status "PENDENTE" no título
5. Envia e-mail avisando a clínica sobre a nova solicitação

Rodar a partir da raiz do projeto com:
    python -m scripts.create_pending_appointment
"""

from datetime import timedelta

from app.check_availability import (
    get_calendar_service,
    calcular_horarios_disponiveis,
    buscar_eventos_periodo,
    evento_para_intervalo,
    slot_tem_conflito,
    CALENDAR_ID,
    DURACAO_CONSULTA_MIN,
)
from app.email_notifier import enviar_email_solicitacao_pendente


def horario_ainda_disponivel(service, horario_inicio):
    """Revalida, na hora de criar o evento, se o slot ainda está livre.
    Protege contra dois pacientes escolherem o mesmo horário quase ao mesmo tempo."""
    horario_fim = horario_inicio + timedelta(minutes=DURACAO_CONSULTA_MIN)

    eventos = buscar_eventos_periodo(
        service,
        horario_inicio - timedelta(minutes=1),
        horario_fim + timedelta(minutes=1),
    )
    intervalos_ocupados = [
        intervalo for e in eventos
        if (intervalo := evento_para_intervalo(e)) is not None
    ]

    return not slot_tem_conflito((horario_inicio, horario_fim), intervalos_ocupados)


def criar_evento_pendente(service, horario_inicio, nome_paciente, telefone_paciente, tipo_consulta="Primeira consulta"):
    """Cria o evento na agenda com status PENDENTE, aguardando aprovação da clínica."""
    horario_fim = horario_inicio + timedelta(minutes=DURACAO_CONSULTA_MIN)

    evento = {
        "summary": f"PENDENTE - {tipo_consulta} - {nome_paciente}",
        "description": (
            f"Solicitação de agendamento via chatbot (AGUARDANDO CONFIRMAÇÃO).\n\n"
            f"Paciente: {nome_paciente}\n"
            f"Telefone: {telefone_paciente}\n"
            f"Tipo de consulta: {tipo_consulta}\n\n"
            f"Ação necessária: confirmar ou recusar este horário e responder ao paciente."
        ),
        "start": {"dateTime": horario_inicio.isoformat()},
        "end": {"dateTime": horario_fim.isoformat()},
    }

    evento_criado = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
    return evento_criado


if __name__ == "__main__":
    service = get_calendar_service()

    disponiveis = calcular_horarios_disponiveis(service, dias_a_frente=7)

    if not disponiveis:
        print("Nenhum horário disponível encontrado.")
        exit()

    print("Horários disponíveis:\n")
    for i, horario in enumerate(disponiveis):
        print(f"{i + 1}. {horario.strftime('%d/%m/%Y %H:%M')} ({horario.strftime('%A')})")

    escolha = int(input("\nDigite o número do horário escolhido (simulando o paciente): ")) - 1
    horario_escolhido = disponiveis[escolha]

    nome_teste = input("Nome do paciente (teste): ")
    telefone_teste = input("Telefone do paciente (teste): ")

    if not horario_ainda_disponivel(service, horario_escolhido):
        print("\n❌ Esse horário acabou de ser ocupado por outra solicitação. Escolha outro.")
        exit()

    evento = criar_evento_pendente(service, horario_escolhido, nome_teste, telefone_teste)

    print(f"\n✅ Evento pendente criado com sucesso!")
    print(f"Link do evento: {evento.get('htmlLink')}")

    enviar_email_solicitacao_pendente(
        nome_paciente=nome_teste,
        telefone_paciente=telefone_teste,
        horario_inicio=horario_escolhido,
        tipo_consulta="Primeira consulta",
        link_evento=evento.get("htmlLink"),
    )