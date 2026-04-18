import sqlite3
import json
import os
import threading
import time

class SQLiteService:
    """Serviço de banco de dados SQLite thread-safe para transmissões."""
    
    _lock = threading.Lock()
    
    def __init__(self, db_path="data/transmissoes.db"):
        self.db_path = db_path
        # Garante que o diretório existe
        diretorio = os.path.dirname(db_path)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        # Limpa arquivos WAL/SHM residuais que causam disk I/O error em rede
        self._limpar_wal()
        self._criar_tabela()
    
    def _limpar_wal(self):
        """Remove arquivos -shm e -wal residuais que travam em drives de rede."""
        for ext in ["-shm", "-wal"]:
            arquivo = self.db_path + ext
            try:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    print(f"[SQLite] Removido arquivo residual: {arquivo}")
            except Exception:
                pass

    def _get_connection(self):
        """Cria uma nova conexão para a thread atual com retry."""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                conn = sqlite3.connect(self.db_path, timeout=15)
                conn.row_factory = sqlite3.Row
                try:
                    # DELETE mode é mais seguro em drives de rede mapeados
                    conn.execute("PRAGMA journal_mode=DELETE")
                except sqlite3.OperationalError:
                    pass
                return conn
            except sqlite3.OperationalError as e:
                if tentativa < max_tentativas - 1:
                    self._limpar_wal()
                    time.sleep(0.5)
                else:
                    raise
    
    def _criar_tabela(self):
        """Cria a tabela de transmissões se não existir."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transmissoes (
                        id TEXT PRIMARY KEY,
                        evento TEXT NOT NULL,
                        data TEXT NOT NULL,
                        horario_inicio TEXT NOT NULL,
                        horario_fim TEXT NOT NULL,
                        responsavel TEXT NOT NULL,
                        tipo_transmissao TEXT,
                        modalidade TEXT,
                        local_evento TEXT DEFAULT '',
                        link_stream TEXT DEFAULT '',
                        link_youtube TEXT DEFAULT '',
                        status TEXT DEFAULT 'Agendado',
                        tempo_total TEXT DEFAULT '00:00:00',
                        publico INTEGER DEFAULT 0,
                        operador TEXT DEFAULT '',
                        observacoes TEXT DEFAULT '',
                        links_adicionais TEXT DEFAULT '[]',
                        data_criacao TEXT DEFAULT ''
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS historico_modificacoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_hora TEXT NOT NULL,
                        usuario TEXT NOT NULL,
                        acao TEXT NOT NULL,
                        detalhes TEXT NOT NULL
                    )
                """)
                conn.commit()
            finally:
                conn.close()
    
    def carregar_todos(self):
        """Carrega todas as transmissões como lista de dicionários."""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            with self._lock:
                try:
                    conn = self._get_connection()
                    try:
                        cursor = conn.execute("SELECT * FROM transmissoes ORDER BY data, horario_inicio")
                        rows = cursor.fetchall()
                        resultado = []
                        for row in rows:
                            d = dict(row)
                            # Converte 'local_evento' de volta para 'local' (nome usado no modelo)
                            d["local"] = d.pop("local_evento", "")
                            # Converte links_adicionais de JSON string para lista
                            try:
                                d["links_adicionais"] = json.loads(d.get("links_adicionais", "[]"))
                            except:
                                d["links_adicionais"] = []
                            resultado.append(d)
                        return resultado
                    finally:
                        conn.close()
                except sqlite3.OperationalError as e:
                    if tentativa < max_tentativas - 1:
                        print(f"[SQLite] Tentativa {tentativa+1} falhou: {e}. Retentando...")
                        self._limpar_wal()
                        time.sleep(1)
                    else:
                        print(f"[SQLite] Todas as tentativas falharam: {e}")
                        return []
    
    def inserir(self, dados):
        """Insere uma nova transmissão."""
        with self._lock:
            conn = self._get_connection()
            try:
                links = json.dumps(dados.get("links_adicionais", []), ensure_ascii=False)
                conn.execute("""
                    INSERT INTO transmissoes 
                    (id, evento, data, horario_inicio, horario_fim, responsavel,
                     tipo_transmissao, modalidade, local_evento, link_stream, link_youtube,
                     status, tempo_total, publico, operador, observacoes, links_adicionais, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dados["id"], dados["evento"], dados["data"],
                    dados["horario_inicio"], dados["horario_fim"], dados["responsavel"],
                    dados.get("tipo_transmissao", ""), dados.get("modalidade", ""),
                    dados.get("local", ""), dados.get("link_stream", ""),
                    dados.get("link_youtube", ""), dados.get("status", "Agendado"),
                    dados.get("tempo_total", "00:00:00"), dados.get("publico", 0),
                    dados.get("operador", ""), dados.get("observacoes", ""),
                    links, dados.get("data_criacao", "")
                ))
                conn.commit()
            finally:
                conn.close()
    
    def atualizar(self, dados):
        """Atualiza uma transmissão existente pelo ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                links = json.dumps(dados.get("links_adicionais", []), ensure_ascii=False)
                conn.execute("""
                    UPDATE transmissoes SET
                        evento=?, data=?, horario_inicio=?, horario_fim=?, responsavel=?,
                        tipo_transmissao=?, modalidade=?, local_evento=?, link_stream=?,
                        link_youtube=?, status=?, tempo_total=?, publico=?, operador=?,
                        observacoes=?, links_adicionais=?, data_criacao=?
                    WHERE id=?
                """, (
                    dados["evento"], dados["data"],
                    dados["horario_inicio"], dados["horario_fim"], dados["responsavel"],
                    dados.get("tipo_transmissao", ""), dados.get("modalidade", ""),
                    dados.get("local", ""), dados.get("link_stream", ""),
                    dados.get("link_youtube", ""), dados.get("status", "Agendado"),
                    dados.get("tempo_total", "00:00:00"), dados.get("publico", 0),
                    dados.get("operador", ""), dados.get("observacoes", ""),
                    links, dados.get("data_criacao", ""),
                    dados["id"]
                ))
                conn.commit()
            finally:
                conn.close()
    
    def deletar(self, id_transmissao):
        """Remove uma transmissão pelo ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("DELETE FROM transmissoes WHERE id=?", (id_transmissao,))
                conn.commit()
            finally:
                conn.close()
    
    def migrar_de_json(self, json_path):
        """Migra dados do arquivo JSON para o SQLite. Retorna True se migrou dados."""
        if not os.path.exists(json_path):
            return False
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                dados_json = json.load(f)
        except:
            return False
        
        if not dados_json:
            return False
        
        # Verifica se já tem dados no SQLite (evita duplicação)
        existentes = self.carregar_todos()
        ids_existentes = {d["id"] for d in existentes}
        
        migrados = 0
        for d in dados_json:
            if d.get("id") and d["id"] not in ids_existentes:
                self.inserir(d)
                migrados += 1
        
        if migrados > 0:
            # Renomeia o JSON como backup
            backup_path = json_path.replace(".json", "_backup.json")
            try:
                import shutil
                shutil.copy2(json_path, backup_path)
                os.remove(json_path) # Remove para não recarregar no futuro
            except Exception as e:
                print(f"[SQLite] Erro ao mover backup: {e}")
            print(f"[SQLite] Migrados {migrados} registros do JSON para SQLite.")
            print(f"[SQLite] Backup criado em: {backup_path}")
        else:
            # Mesmo se não houve registros migrados novos (ex: já foi migrado antes mas falhou ao apagar)
            # deve apagar ou renomear se foi backup feito.
            backup_path = json_path.replace(".json", "_backup.json")
            try:
                import shutil
                shutil.copy2(json_path, backup_path)
                os.remove(json_path)
            except:
                pass
        
        return migrados > 0

    def registrar_historico(self, acao: str, detalhes: str):
        from datetime import datetime
        import os
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        usuario = os.environ.get("USERNAME", "Desconhecido")
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    INSERT INTO historico_modificacoes (data_hora, usuario, acao, detalhes)
                    VALUES (?, ?, ?, ?)
                """, (agora, usuario, acao, detalhes))
                conn.commit()
            except Exception as e:
                print("Erro ao registrar histórico:", e)
            finally:
                conn.close()

    def obter_historico_modificacoes(self):
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM historico_modificacoes ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                print("Erro ao obter histórico:", e)
                return []
            finally:
                conn.close()
