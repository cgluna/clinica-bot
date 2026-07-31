"""
Módulo: envia e-mail informativo pra clínica quando um agendamento pendente é criado.

Usa SMTP do Gmail com Senha de app (não a senha normal da conta).
"""

import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # carrega as variáveis do arquivo .env

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA_APP = os.getenv("EMAIL_SENHA_APP")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")

SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587


def enviar_email_solicitacao_pendente(nome_paciente, telefone_paciente, horario_inicio, tipo_consulta, link_evento):
    """Envia e-mail avisando sobre uma nova solicitação de agendamento pendente."""

    assunto = f"Nova solicitação de agendamento - {nome_paciente}"

    corpo = f"""
Uma nova solicitação de agendamento foi recebida via chatbot.

Paciente: {nome_paciente}
Telefone: {telefone_paciente}
Tipo de consulta: {tipo_consulta}
Horário solicitado: {horario_inicio.strftime('%d/%m/%Y %H:%M')}

O horário já está bloqueado na agenda como PENDENTE.
Confira o evento e responda ao paciente para confirmar ou recusar:
{link_evento}
""".strip()

    mensagem = MIMEText(corpo, "plain", "utf-8")
    mensagem["Subject"] = assunto
    mensagem["From"] = EMAIL_REMETENTE
    mensagem["To"] = EMAIL_DESTINATARIO

    with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA) as servidor:
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, mensagem.as_string())

    print(f"✅ E-mail enviado para {EMAIL_DESTINATARIO}")


if __name__ == "__main__":
    # Teste isolado: dispara um e-mail de exemplo, sem precisar criar evento real
    from datetime import datetime

    enviar_email_solicitacao_pendente(
        nome_paciente="Paciente Teste",
        telefone_paciente="(81) 99999-9999",
        horario_inicio=datetime.now(),
        tipo_consulta="Primeira consulta",
        link_evento="https://calendar.google.com/exemplo",
    )