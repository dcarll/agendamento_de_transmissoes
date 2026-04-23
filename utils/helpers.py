from datetime import datetime
import flet as ft
from functools import lru_cache

def calcular_duracao(inicio, fim):
    """Calcula a duração total entre horário de início e fim no formato HH:MM."""
    try:
        fmt = "%H:%M"
        t_inicio = datetime.strptime(inicio, fmt)
        t_fim = datetime.strptime(fim, fmt)
        delta = t_fim - t_inicio
        segundos = delta.total_seconds()
        
        if segundos < 0:
            # Se o fim for no dia seguinte (ex: 23:00 às 01:00)
            segundos += 86400 
        
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segundos = int(segundos % 60)
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    except Exception:
        return "00:00:00"

def converter_tempo_para_segundos(tempo_str):
    """Converte string HH:MM:SS para total de segundos."""
    try:
        if not tempo_str: return 0
        partes = tempo_str.split(':')
        if len(partes) == 3:
            h, m, s = map(int, partes)
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            h, m = map(int, partes)
            return h * 3600 + m * 60
        return 0
    except:
        return 0

def formatar_segundos_para_tempo(segundos):
    """Converte total de segundos em string HH:MM:SS."""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def validar_hora(hora_str):
    """Valida se a string está no formato HH:MM."""
    try:
        datetime.strptime(hora_str, "%H:%M")
        return True
    except:
        return False

@lru_cache(maxsize=500)
def parse_date(data_str):
    """Tenta converter uma string de data em objeto datetime suportando múltiplos formatos."""
    if not data_str: return None
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]
    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt)
        except:
            continue
    return None

@lru_cache(maxsize=500)
def normalize_date(data_str):
    """Converte qualquer formato de data para o padrão YYYY-MM-DD."""
    dt = parse_date(data_str)
    if dt:
        return dt.strftime("%Y-%m-%d")
    return data_str

def format_date_br(data_str):
    """Converte YYYY-MM-DD para DD/MM/YYYY."""
    dt = parse_date(data_str)
    if dt:
        return dt.strftime("%d/%m/%Y")
    return data_str

def formatar_data_semana(data_str):
    """Retorna a data formatada com o dia da semana em português (Ex: 08/04 - Qua)."""
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    dt = parse_date(data_str)
    if dt:
        dia_semana = dias[dt.weekday()]
        return f"{dt.strftime('%d/%m')} - {dia_semana}"
    return data_str

def formatar_data_completa_semana(data_str):
    """Retorna a data completa com o dia da semana (Ex: 08/04/2026 - Quarta-feira)."""
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dt = parse_date(data_str)
    if dt:
        dia_semana = dias[dt.weekday()]
        return f"{dt.strftime('%d/%m/%Y')} ({dia_semana})"

# Cache para as configurações de status para evitar recriação constante
_STATUS_CONFIG = {
    "Aguardando (Fase 1)": {
        "label": "Aguardando",
        "phase": "fase 1",
        "color": ft.Colors.RED_400,
        "icon": ft.Icons.SCHEDULE
    },
    "Em Reunião (Fase 2)": {
        "label": "Em Reunião",
        "phase": "fase 2",
        "color": ft.Colors.AMBER_400,
        "icon": ft.Icons.GROUPS
    },
    "Criação de Links (Fase 3)": {
        "label": "Criação de Links",
        "phase": "fase 3",
        "color": ft.Colors.TEAL_400,
        "icon": ft.Icons.LINK
    },
    "Agendado (Fase 4)": {
        "label": "Agendado",
        "phase": "fase 4",
        "color": ft.Colors.GREEN_400,
        "icon": ft.Icons.EVENT_AVAILABLE
    },
    "Finalizado (Fase 5)": {
        "label": "Finalizado",
        "phase": "fase 5",
        "color": ft.Colors.PURPLE_400,
        "icon": ft.Icons.CHECK_CIRCLE
    },
    "Cancelado": {
        "label": "Cancelado",
        "phase": "cancelado",
        "color": ft.Colors.BROWN,
        "icon": ft.Icons.CANCEL
    }
}

_LEGACY_MAP = {
    "Em andamento": "Aguardando (Fase 1)",
    "Agendado (Fase 1)": "Aguardando (Fase 1)",
    "Agendado": "Em Reunião (Fase 2)",
    "Agendado e Criado": "Criação de Links (Fase 3)",
    "Finalizado": "Finalizado (Fase 5)"
}

def get_status_info(status):
    """Retorna as informações de cores e fases para cada status."""
    normalized_status = _LEGACY_MAP.get(status, status)
    return _STATUS_CONFIG.get(normalized_status, {
        "label": status,
        "phase": "",
        "color": ft.Colors.WHITE24,
        "icon": ft.Icons.QUESTION_MARK
    })

def get_status_options():
    """Retorna a lista de nomes de status para os dropdowns."""
    return [
        "Aguardando (Fase 1)",
        "Em Reunião (Fase 2)",
        "Criação de Links (Fase 3)",
        "Agendado (Fase 4)",
        "Finalizado (Fase 5)",
        "Cancelado"
    ]

def check_status_match(status, filtro):
    """Verifica se o status bate com o filtro selecionado (considerando phases e legados)."""
    if not filtro or filtro == "Todos":
        return True
    
    # Se o filtro não for uma opção de status conhecida, não aplicamos o match por status aqui
    # Isso permite que a busca por texto (ex: nome do evento) continue funcionando no mesmo campo
    options = get_status_options()
    if filtro not in options:
        return False
        
    info_s = get_status_info(status)
    info_f = get_status_info(filtro)
    
    return info_s["phase"] == info_f["phase"]
