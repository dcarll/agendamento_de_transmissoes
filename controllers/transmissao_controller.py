import csv
from models.transmissao_model import Transmissao
from services.sqlite_service import SQLiteService
from utils.helpers import calcular_duracao, converter_tempo_para_segundos, formatar_segundos_para_tempo
from datetime import datetime
import os

class TransmissaoController:
    FILEPATH = os.path.join("data", "transmissoes.json")  # Mantido para migração
    DB_PATH = os.path.join("data", "transmissoes.db")

    def __init__(self, on_change=None):
        self.on_change = on_change
        self.db = SQLiteService(self.DB_PATH)
        
        # Migração automática: JSON → SQLite (apenas na primeira execução)
        if os.path.exists(self.FILEPATH):
            migrou = self.db.migrar_de_json(self.FILEPATH)
            if migrou:
                print("[Controller] Dados migrados do JSON para SQLite com sucesso!")
        
        self.transmissoes = self.carregar()

    def carregar(self):
        """Carrega a lista de transmissões do SQLite."""
        dados = self.db.carregar_todos()
        return [Transmissao.from_dict(d) for d in dados]

    def salvar(self):
        """Notifica que houve mudança (dados já foram salvos diretamente no SQLite)."""
        if self.on_change:
            self.on_change()

    def adicionar(self, transmissao: Transmissao):
        """Adiciona uma nova transmissão e calcula a duração."""
        transmissao.tempo_total = calcular_duracao(transmissao.horario_inicio, transmissao.horario_fim)
        self.db.inserir(transmissao.to_dict())
        self.transmissoes.append(transmissao)
        
        detalhes = f"Evento: {transmissao.evento} ({transmissao.data} as {transmissao.horario_inicio})"
        self.db.registrar_historico("INSERÇÃO", detalhes)
        
        self.salvar()

    def atualizar(self, transmissao_atualizada: Transmissao):
        """Atualiza os dados de uma transmissão existente."""
        transmissao_atualizada.tempo_total = calcular_duracao(
            transmissao_atualizada.horario_inicio, 
            transmissao_atualizada.horario_fim
        )
        
        old_t = next((t for t in self.transmissoes if t.id == transmissao_atualizada.id), None)
        
        self.db.atualizar(transmissao_atualizada.to_dict())
        for i, t in enumerate(self.transmissoes):
            if t.id == transmissao_atualizada.id:
                self.transmissoes[i] = transmissao_atualizada
                break
                
        if old_t:
            mudancas = []
            old_dict = old_t.to_dict()
            new_dict = transmissao_atualizada.to_dict()
            for key, old_val in old_dict.items():
                if key in ["links_adicionais", "id", "data_criacao"]: continue
                new_val = new_dict.get(key)
                if old_val != new_val:
                    chave_fmt = key.replace("_", " ").title()
                    val_antigo = str(old_val)[:30] + "..." if isinstance(old_val, str) and len(str(old_val)) > 30 else old_val
                    val_novo = str(new_val)[:30] + "..." if isinstance(new_val, str) and len(str(new_val)) > 30 else new_val
                    mudancas.append(f"{chave_fmt}: {val_antigo} -> {val_novo}")
            
            diff_str = " | ".join(mudancas)
            if not diff_str:
                diff_str = "Salvo sem mudanças perceptíveis."
            detalhes = f"Evento: {transmissao_atualizada.evento} - {diff_str}"
        else:
            detalhes = f"Evento: {transmissao_atualizada.evento} ({transmissao_atualizada.data} as {transmissao_atualizada.horario_inicio})"

        self.db.registrar_historico("ALTERAÇÃO", detalhes)
        
        self.salvar()

    def deletar(self, id_transmissao):
        """Remove uma transmissão pelo ID."""
        t_del = next((t for t in self.transmissoes if t.id == id_transmissao), None)
        if t_del:
            detalhes = f"Evento: {t_del.evento} ({t_del.data} as {t_del.horario_inicio})"
        else:
            detalhes = "Evento excluído (Dados não encontrados)"

        self.db.deletar(id_transmissao)
        self.transmissoes = [t for t in self.transmissoes if t.id != id_transmissao]
        
        self.db.registrar_historico("EXCLUSÃO", detalhes)
        
        self.salvar()

    def get_stats(self):
        """Calcula estatísticas para o dashboard."""
        agora = datetime.now()
        mes_atual = agora.month
        ano_atual = agora.year
        hoje_str = agora.strftime("%Y-%m-%d")

        # Mapeamento para contagem (considerando legados e novos nomes)
        def is_status(t, target_key):
            # No helpers definimos o mapeamento:
            # Em andamento -> Agendado (Fase 1)
            # Agendado -> Em Reunião (Fase 2)
            # Agendado e Criado -> Criação de Links (Fase 3)
            # ...
            # Agendado (Fase 4)
            map_keys = {
                "f1": ["Em andamento", "Agendado (Fase 1)", "Aguardando", "Aguardando (Fase 1)"],
                "f2": ["Agendado", "Em Reunião (Fase 2)"],
                "f3": ["Agendado e Criado", "Criação de Links (Fase 3)"],
                "f4": ["Agendado (Fase 4)"],
                "f5": ["Finalizado", "Finalizado (Fase 5)"],
                "cancelados": ["Cancelado"]
            }
            return t.status in map_keys.get(target_key, [])

        ativas = [t for t in self.transmissoes if is_status(t, "f1")]
        em_reuniao = [t for t in self.transmissoes if is_status(t, "f2") and t.data >= hoje_str]
        criacao_links = [t for t in self.transmissoes if is_status(t, "f3") and t.data >= hoje_str]
        agendado_f4 = [t for t in self.transmissoes if is_status(t, "f4") and t.data >= hoje_str]
        concluidas = [t for t in self.transmissoes if is_status(t, "f5")]
        cancelados = [t for t in self.transmissoes if is_status(t, "cancelados")]
        
        total_mes = 0
        segundos_mes = 0
        publico_mes = 0
        segundos_totais = 0
        publico_acumulado = 0

        from utils.helpers import parse_date 
        for t in self.transmissoes:
            dt = parse_date(t.data)
            # Estatísticas Mensais
            if dt and dt.month == mes_atual and dt.year == ano_atual:
                if not is_status(t, "cancelados"):
                    total_mes += 1
                
                if is_status(t, "f5"):
                    segundos_mes += converter_tempo_para_segundos(t.tempo_total)
                    publico_mes += t.publico
            
            # Estatísticas Acumuladas
            if is_status(t, "f5"):
                segundos_totais += converter_tempo_para_segundos(t.tempo_total)
                publico_acumulado += t.publico

        total_semestre = 0
        segundos_semestre = 0
        publico_semestre = 0
        mes_atual = agora.month
        semestre_atual_range = range(1, 7) if mes_atual <= 6 else range(7, 13)

        for t in self.transmissoes:
            dt = parse_date(t.data)
            if not dt or dt.year != agora.year: continue
            
            if dt.month in semestre_atual_range:
                if not is_status(t, "cancelados"):
                    total_semestre += 1
                
                if is_status(t, "f5"):
                    segundos_semestre += converter_tempo_para_segundos(t.tempo_total)
                    publico_semestre += t.publico

        total_ano = 0
        segundos_ano = 0
        publico_ano = 0

        for t in self.transmissoes:
            dt = parse_date(t.data)
            if not dt or dt.year != agora.year: continue
            
            if not is_status(t, "cancelados"):
                total_ano += 1
            
            if is_status(t, "f5"):
                segundos_ano += converter_tempo_para_segundos(t.tempo_total)
                publico_ano += t.publico

        return {
            "ativas": len(ativas),
            "em_reuniao": len(em_reuniao),
            "criacao_links": len(criacao_links),
            "agendado_f4": len(agendado_f4),
            "concluidas": len(concluidas),
            "cancelados": len(cancelados),
            "total_mensal": total_mes,
            "horas_mensal": formatar_segundos_para_tempo(segundos_mes),
            "publico_mensal": publico_mes,
            "horas_totais": formatar_segundos_para_tempo(segundos_totais),
            "publico_total": publico_acumulado,
            "total_semestre": total_semestre,
            "horas_semestre": formatar_segundos_para_tempo(segundos_semestre),
            "publico_semestre": publico_semestre,
            "total_ano": total_ano,
            "horas_ano": formatar_segundos_para_tempo(segundos_ano),
            "publico_ano": publico_ano
        }

    def exportar_csv(self, caminho_csv):
        """Exporta todas as transmissões para um arquivo CSV."""
        if not self.transmissoes:
            return False
        
        try:
            campos = list(self.transmissoes[0].to_dict().keys())
            with open(caminho_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                for t in self.transmissoes:
                    writer.writerow(t.to_dict())
            return True
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False
