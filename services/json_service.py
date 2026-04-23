import json
import os
import threading

class JsonService:
    """
    Serviço de dados JSON - carrega uma vez, opera em memória, salva atomicamente.
    Padrão idêntico ao projeto de agendamento de aulas que funciona na rede.
    """
    
    _lock = threading.Lock()
    
    def __init__(self, file_path="data/transmissoes.json"):
        self.file_path = file_path
        self.history_path = file_path.replace(".json", "_history.json")
        diretorio = os.path.dirname(file_path)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Carrega TUDO na memória uma única vez
        self._dados = self._carregar_arquivo()

    def _carregar_arquivo(self):
        """Lê o arquivo JSON do disco. Chamado apenas na inicialização."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[JSON] Erro ao carregar: {e}")
            return []

    def _salvar_arquivo(self):
        """Gravação atômica: salva em .tmp e renomeia. Nunca corrompe o original."""
        conteudo = json.dumps(self._dados, ensure_ascii=False, indent=2)
        temp_path = self.file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
        except Exception as e:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            print(f"[JSON] Erro ao salvar: {e}")

    def carregar_todos(self):
        """Retorna os dados da memória (sem tocar no disco)."""
        return self._dados

    def salvar_todos(self, lista_dados):
        """Atualiza a memória e persiste no disco atomicamente."""
        with self._lock:
            self._dados = lista_dados
            self._salvar_arquivo()

    def registrar_historico(self, acao, detalhes):
        """Mantém o histórico em arquivo separado."""
        from datetime import datetime
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        usuario = os.environ.get("USERNAME", "Desconhecido")
        
        with self._lock:
            try:
                historico = []
                if os.path.exists(self.history_path):
                    with open(self.history_path, "r", encoding="utf-8") as f:
                        historico = json.load(f)
                
                historico.insert(0, {
                    "data_hora": agora,
                    "usuario": usuario,
                    "acao": acao,
                    "detalhes": detalhes
                })
                historico = historico[:500]
                
                temp = self.history_path + ".tmp"
                with open(temp, "w", encoding="utf-8") as f:
                    json.dump(historico, f, indent=2, ensure_ascii=False)
                if os.path.exists(self.history_path):
                    os.replace(temp, self.history_path)
                else:
                    os.rename(temp, self.history_path)
            except Exception as e:
                print(f"[JSON] Erro no histórico: {e}")

    def obter_historico(self):
        if not os.path.exists(self.history_path):
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
