"""
Script: calcula os horários disponíveis para agendamento.

Regras:
- Consultas de 45 minutos
- Buffer de 5 minutos entre consultas
- Expediente: 8h às 18h
- Intervalo de almoço: 12h às 13h (nenhum slot é oferecido nesse período)
- Dias considerados: segunda a sexta
- Um horário só é oferecido se não colidir com nenhum evento já existente na agenda
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta, time, timezone

# --- Configurações ---
CREDENTIALS_FILE = "credentials.json"
CALENDAR_ID = "gabriel.lunnaa7@gmail.com"  # troque pelo seu e-mail (mesmo usado no script anterior)
SCOPES = ["https://www.googleapis.com/auth/calendar"]

DURACAO_CONSULTA_MIN = 45
BUFFER_ENTRE_CONSULTAS_MIN = 5
HORA_INICIO_EXPEDIENTE = time(8, 0)
HORA_FIM_EXPEDIENTE = time(18, 0)
HORA_INICIO_ALMOCO = time(12, 0)
HORA_FIM_ALMOCO = time(13, 0)
DIAS_CONSIDERADOS = [0, 1, 2, 3, 4]  # 0=segunda ... 4=sexta (segunda a sexta)


def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)


def buscar_eventos_periodo(service, data_inicio, data_fim):
    """Busca todos os eventos existentes entre duas datas."""
    resultado = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=data_inicio.isoformat(),
        timeMax=data_fim.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return resultado.get("items", [])


def evento_para_intervalo(evento):
    """Extrai (inicio, fim) de um evento no formato datetime."""
    inicio_str = evento["start"].get("dateTime")
    fim_str = evento["end"].get("dateTime")

    # Ignora eventos de dia inteiro (sem horário definido, ex: feriados)
    if not inicio_str or not fim_str:
        return None

    inicio = datetime.fromisoformat(inicio_str)
    fim = datetime.fromisoformat(fim_str)
    return (inicio, fim)


def gerar_grade_horarios(data_base, timezone_local):
    """Gera todos os slots possíveis de um dia, respeitando duração, expediente,
    intervalo de almoço e buffer entre consultas."""
    slots = []
    inicio_dia = datetime.combine(data_base, HORA_INICIO_EXPEDIENTE, tzinfo=timezone_local)
    fim_dia = datetime.combine(data_base, HORA_FIM_EXPEDIENTE, tzinfo=timezone_local)
    inicio_almoco = datetime.combine(data_base, HORA_INICIO_ALMOCO, tzinfo=timezone_local)
    fim_almoco = datetime.combine(data_base, HORA_FIM_ALMOCO, tzinfo=timezone_local)

    slot_atual = inicio_dia
    while slot_atual + timedelta(minutes=DURACAO_CONSULTA_MIN) <= fim_dia:
        slot_fim = slot_atual + timedelta(minutes=DURACAO_CONSULTA_MIN)

        # Pula slots que colidem com o intervalo de almoço
        if slot_atual < fim_almoco and slot_fim > inicio_almoco:
            slot_atual = fim_almoco  # pula direto pro fim do almoço
            continue

        slots.append((slot_atual, slot_fim))
        # próximo slot começa após o fim deste + buffer
        slot_atual = slot_fim + timedelta(minutes=BUFFER_ENTRE_CONSULTAS_MIN)

    return slots


def slot_tem_conflito(slot, eventos_ocupados):
    """Verifica se um slot colide com algum evento já existente."""
    slot_inicio, slot_fim = slot
    for evento_inicio, evento_fim in eventos_ocupados:
        # Colisão: slot começa antes do evento acabar E slot termina depois do evento começar
        if slot_inicio < evento_fim and slot_fim > evento_inicio:
            return True
    return False


def calcular_horarios_disponiveis(service, dias_a_frente=7):
    """Retorna uma lista de horários livres para os próximos N dias."""
    agora = datetime.now(timezone.utc).astimezone()
    tz_local = agora.tzinfo

    data_inicio_busca = agora
    data_fim_busca = agora + timedelta(days=dias_a_frente)

    eventos = buscar_eventos_periodo(service, data_inicio_busca, data_fim_busca)
    intervalos_ocupados = [
        intervalo for e in eventos
        if (intervalo := evento_para_intervalo(e)) is not None
    ]

    horarios_disponiveis = []

    for i in range(dias_a_frente):
        dia = (agora + timedelta(days=i)).date()

        if dia.weekday() not in DIAS_CONSIDERADOS:
            continue

        slots_do_dia = gerar_grade_horarios(dia, tz_local)

        for slot in slots_do_dia:
            slot_inicio, slot_fim = slot

            # Não oferece horário que já passou (se for hoje)
            if slot_inicio < agora:
                continue

            if not slot_tem_conflito(slot, intervalos_ocupados):
                horarios_disponiveis.append(slot_inicio)

    return horarios_disponiveis


if __name__ == "__main__":
    try:
        service = get_calendar_service()
        disponiveis = calcular_horarios_disponiveis(service, dias_a_frente=7)

        if not disponiveis:
            print("Nenhum horário disponível encontrado nos próximos 7 dias.")
        else:
            print(f"Horários disponíveis nos próximos 7 dias ({len(disponiveis)} encontrados):\n")
            for horario in disponiveis:
                dia_semana = horario.strftime("%A")
                print(f"- {horario.strftime('%d/%m/%Y %H:%M')} ({dia_semana})")

    except Exception as e:
        print("❌ Erro ao calcular disponibilidade:")
        print(e)