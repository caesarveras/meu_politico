import inspect
from collections.abc import Callable
from typing import Any

from app.services.camara_client import CamaraClient, camara_client


class SyncCollectorService:
    def __init__(self, client: CamaraClient | None = None) -> None:
        self.client = client or camara_client

    def set_raw_recorder(self, recorder: Callable[[str, str, dict | None, dict], Any] | None) -> None:
        self.client.set_raw_recorder(recorder)

    def clear_raw_recorder(self) -> None:
        self.client.clear_raw_recorder()

    async def fetch_deputados(self, itens: int = 100, all_pages: bool = False) -> list[dict]:
        return await self.client.fetch_deputados(itens=itens, all_pages=all_pages)

    async def fetch_deputados_historicos(self) -> list[dict]:
        return await self.client.fetch_deputados_historicos()

    async def fetch_legislaturas(self) -> list[dict]:
        return await self.client.fetch_legislaturas()

    async def fetch_orgaos_deputados_por_legislatura(self, legislatura: int) -> list[dict]:
        return await self.client.fetch_orgaos_deputados_por_legislatura(legislatura)

    async def fetch_proposicoes_por_ano_download(self, ano: int) -> list[dict]:
        return await self.client.fetch_proposicoes_por_ano_download(ano)

    async def fetch_proposicoes_autores_por_ano_download(self, ano: int) -> list[dict]:
        return await self.client.fetch_proposicoes_autores_por_ano_download(ano)

    async def fetch_proposicoes_temas_por_ano_download(self, ano: int) -> list[dict]:
        return await self.client.fetch_proposicoes_temas_por_ano_download(ano)

    async def fetch_deputado(self, deputado_id: int) -> dict:
        return await self.client.fetch_deputado(deputado_id)

    async def fetch_deputado_historico(self, deputado_id: int) -> list[dict]:
        return await self.client.fetch_deputado_historico(deputado_id)

    async def fetch_deputado_eventos(self, deputado_id: int) -> list[dict]:
        return await self.client.fetch_deputado_eventos(deputado_id)

    async def fetch_deputado_mandatos_externos(self, deputado_id: int) -> list[dict]:
        return await self.client.fetch_deputado_mandatos_externos(deputado_id)

    async def fetch_proposicoes(self, itens: int = 100, ano_inicio: int | None = None, ano_fim: int | None = None, all_pages: bool = False) -> list[dict]:
        return await self.client.fetch_proposicoes(itens=itens, ano_inicio=ano_inicio, ano_fim=ano_fim, all_pages=all_pages)

    async def fetch_proposicao(self, proposicao_id: int) -> dict:
        return await self.client.fetch_proposicao(proposicao_id)

    async def fetch_tramitacoes(self, proposicao_id: int, itens: int = 100, all_pages: bool = True) -> list[dict]:
        return await self.client.fetch_tramitacoes(proposicao_id, itens=itens, all_pages=all_pages)

    async def fetch_votacoes(self, proposicao_id: int, itens: int = 100, all_pages: bool = True) -> list[dict]:
        return await self.client.fetch_votacoes(proposicao_id, itens=itens, all_pages=all_pages)

    async def fetch_votacao_votos(self, votacao_id: str, itens: int = 100, all_pages: bool = True) -> list[dict]:
        return await self.client.fetch_votacao_votos(votacao_id, itens=itens, all_pages=all_pages)


sync_collector = SyncCollectorService()
