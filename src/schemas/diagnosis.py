from pydantic import BaseModel, Field
from typing import List, Optional

class DiagnosticReport(BaseModel):
    simbolo_identificado: str = Field(description='Nome ou descrição da luz de alerta identificada no painel')
    gravidade_urgencia: str = Field(description='Nível de urgência: Baixo, Médio, Alto ou Crítico')
    significado_manual: str = Field(description='Explicação clara do significado do alerta com base no manual do veículo')
    prognostico_contextual: str = Field(description='Análise integrando os relatos do motorista (velocidade, clima, sons, etc.)')
    acoes_recomendadas: List[str] = Field(description='Lista de passos ou ações imediatas recomendadas ao motorista')
    resumo_oficina: str = Field(description='Síntese técnica pronta para ser enviada para a concessionária ou mecânico')
