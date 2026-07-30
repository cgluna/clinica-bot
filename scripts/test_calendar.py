"""
Script de teste: verifica se a autenticação com a Google Calendar API
está funcionando, listando os próximos eventos da agenda.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timezone

# --- Configurações ---
CREDENTIALS_FILE = "credentials.json"  # caminho pro JSON da service account
CALENDAR_ID = "gabriel.lunnaa7@gmail.com"  # "primary" = sua agenda principal. Pode trocar pelo e-mail de outra agenda específica.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """Autentica usando a Service Account e retorna o objeto de serviço da API."""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=credentials)
    return service


def listar_proximos_eventos(service, max_resultados=10):
    """Lista os próximos eventos da agenda configurada."""
    agora = datetime.now(timezone.utc).isoformat()

    resultado = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=agora,
        maxResults=max_resultados,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    eventos = resultado.get("items", [])

    if not eventos:
        print("Nenhum evento futuro encontrado. (Isso é normal se a agenda estiver vazia)")
        return

    print(f"Próximos {len(eventos)} evento(s):\n")
    for evento in eventos:
        inicio = evento["start"].get("dateTime", evento["start"].get("date"))
        titulo = evento.get("summary", "(sem título)")
        print(f"- {inicio} | {titulo}")


if __name__ == "__main__":
    try:
        service = get_calendar_service()
        print("✅ Autenticação bem-sucedida!\n")
        listar_proximos_eventos(service)
    except Exception as e:
        print("❌ Erro ao conectar com a Google Calendar API:")
        print(e)