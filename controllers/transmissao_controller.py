import csv
from models.transmissao_model import Transmissao
from services.json_service import JsonService
from utils.helpers import calcular_duracao, converter_tempo_para_segundos, formatar_segundos_para_tempo, parse_date, normalize_date
from datetime import datetime, timedelta
import os

class TransmissaoController:
    FILEPATH = os.path.join("data", "transmissoes.json")

    def __init__(self, on_change=None):
        self.on_change = on_change
        self.db = JsonService(self.FILEPATH)
        self.transmissoes = []
        self.carregar()

    def carregar(self):
        dados = self.db.carregar_todos()
        self.transmissoes = [Transmissao.from_dict(d) for d in dados]
        return self.transmissoes

    def salvar(self):
        if self.on_change: self.on_change()

    def adicionar(self, t: Transmissao):
        t.tempo_total = calcular_duracao(t.horario_inicio, t.horario_fim)
        self.transmissoes.append(t)
        self.db.salvar_todos([item.to_dict() for item in self.transmissoes])
        self.db.registrar_historico("INSERÇÃO", f"Evento: {t.evento}")
        self.salvar()

    def atualizar(self, t_new: Transmissao):
        t_new.tempo_total = calcular_duracao(t_new.horario_inicio, t_new.horario_fim)
        for i, t in enumerate(self.transmissoes):
            if t.id == t_new.id: self.transmissoes[i] = t_new; break
        self.db.salvar_todos([item.to_dict() for item in self.transmissoes])
        self.db.registrar_historico("ALTERAÇÃO", f"Evento: {t_new.evento}")
        self.salvar()

    def deletar(self, id_t):
        self.transmissoes = [t for t in self.transmissoes if t.id != id_t]
        self.db.salvar_todos([item.to_dict() for item in self.transmissoes])
        self.db.registrar_historico("EXCLUSÃO", f"ID: {id_t}")
        self.salvar()

    def get_estatisticas(self):
        agora = datetime.now(); hoje_str = agora.strftime("%Y-%m-%d")
        stats = {
            "f1": 0, "f2": 0, "f3": 0, "f4": 0, "f5": 0,
            "total_mes": 0, "horas_mes": 0, "publico_mes": 0,
            "total_semestre": 0, "horas_semestre": 0, "publico_semestre": 0,
            "total_ano": 0, "horas_ano": 0, "publico_ano": 0,
            "publico_total": 0, "horas_totais": 0
        }
        
        from utils.helpers import get_status_info
        for t in self.transmissoes:
            dt = parse_date(t.data); s_info = get_status_info(t.status); phase = s_info["phase"]
            seg = converter_tempo_para_segundos(t.tempo_total)
            
            if phase == "fase 1": stats["f1"] += 1
            elif phase == "fase 2": stats["f2"] += 1
            elif phase == "fase 3": stats["f3"] += 1
            elif phase == "fase 4": stats["f4"] += 1
            elif phase == "fase 5": stats["f5"] += 1
            
            if dt:
                # Mensal
                if dt.month == agora.month and dt.year == agora.year:
                    stats["total_mes"] += 1; stats["horas_mes"] += seg; stats["publico_mes"] += t.publico
                # Semestral
                sem_atual = 1 if agora.month <= 6 else 2; t_sem = 1 if dt.month <= 6 else 2
                if sem_atual == t_sem and dt.year == agora.year:
                    stats["total_semestre"] += 1; stats["horas_semestre"] += seg; stats["publico_semestre"] += t.publico
                # Anual
                if dt.year == agora.year:
                    stats["total_ano"] += 1; stats["horas_ano"] += seg; stats["publico_ano"] += t.publico
            
            if phase == "fase 5":
                stats["publico_total"] += t.publico; stats["horas_totais"] += seg
        
        # Formatação
        stats["horas_mes"] = formatar_segundos_para_tempo(stats["horas_mes"])
        stats["horas_semestre"] = formatar_segundos_para_tempo(stats["horas_semestre"])
        stats["horas_ano"] = formatar_segundos_para_tempo(stats["horas_ano"])
        stats["horas_totais"] = formatar_segundos_para_tempo(stats["horas_totais"])
        return stats
