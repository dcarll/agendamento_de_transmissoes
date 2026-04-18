import json
import os

class JSONService:
    @staticmethod
    def carregar_dados(caminho_arquivo):
        """Carrega dados de um arquivo JSON. Retorna lista vazia se não existir ou houver erro."""
        if not os.path.exists(caminho_arquivo):
            return []
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def salvar_dados(caminho_arquivo, dados):
        """Salva uma lista de dados em um arquivo JSON."""
        # Garante que o diretório existe
        diretorio = os.path.dirname(caminho_arquivo)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
            
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    @staticmethod
    def get_last_modified(caminho_arquivo):
        """Retorna o timestamp da última modificação do arquivo."""
        if os.path.exists(caminho_arquivo):
            return os.path.getmtime(caminho_arquivo)
        return 0
