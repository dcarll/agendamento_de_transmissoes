import uuid
from datetime import datetime
from dataclasses import dataclass, asdict, field

@dataclass
class Transmissao:
    evento: str
    data: str
    horario_inicio: str
    horario_fim: str
    responsavel: str
    tipo_transmissao: str # StreamYard, OBS, YouTube, Zoom
    modalidade: str # Presencial, Online, Híbrido
    local: str
    link_stream: str = ""
    link_youtube: str = ""
    status: str = "Agendado" # Agendado, Em andamento, Finalizado
    tempo_total: str = "00:00:00"
    publico: int = 0
    operador: str = ""
    observacoes: str = ""
    links_adicionais: list = field(default_factory=list) # Lista de dicionários {"label": str, "url": str}
    data_criacao: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        # Remove ID do dicionário se quiser gerar um novo, mas aqui queremos manter o existente
        return cls(**data)
