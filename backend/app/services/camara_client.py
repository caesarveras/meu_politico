import httpx

from app.core.config import settings


class CamaraClient:
    def __init__(self) -> None:
        self._raw_recorder = None

    @staticmethod
    def _download_url(path: str) -> str:
        return f"https://dadosabertos.camara.leg.br/arquivos{path}"

    def set_raw_recorder(self, recorder) -> None:
        self._raw_recorder = recorder

    def clear_raw_recorder(self) -> None:
        self._raw_recorder = None

    @staticmethod
    def _extract_total_pages(payload: dict) -> int | None:
        links = payload.get("links") if isinstance(payload.get("links"), list) else []
        for link in links:
            if not isinstance(link, dict):
                continue
            if link.get("rel") != "last":
                continue
            href = str(link.get("href") or "")
            if "pagina=" not in href:
                continue
            page_value = href.split("pagina=")[-1].split("&")[0]
            if page_value.isdigit():
                return int(page_value)
        return None

    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{settings.camara_api_base_url}{path}"
        last_error: Exception | None = None
        for _ in range(2):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    if self._raw_recorder is not None:
                        self._raw_recorder(path, url, params, payload)
                    return payload
            except httpx.HTTPError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        return {}

    async def _get_download_json(self, path: str) -> list[dict] | dict:
        url = self._download_url(path)
        last_error: Exception | None = None
        for _ in range(2):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    if self._raw_recorder is not None:
                        self._raw_recorder(path, url, None, payload)
                    return payload
            except httpx.HTTPError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        return []

    async def _get_all_pages(self, path: str, params: dict | None = None, page_size: int = 100) -> list[dict]:
        base_params = {**(params or {}), "itens": page_size}
        first_payload = await self._get(path, params={**base_params, "pagina": 1})
        dados = list(first_payload.get("dados", []))
        total_pages = self._extract_total_pages(first_payload)
        if total_pages is None:
            if len(dados) < page_size:
                return dados
            current_page = 2
            while True:
                payload = await self._get(path, params={**base_params, "pagina": current_page})
                page_data = payload.get("dados", [])
                if not page_data:
                    break
                dados.extend(page_data)
                if len(page_data) < page_size:
                    break
                current_page += 1
            return dados

        for page in range(2, total_pages + 1):
            payload = await self._get(path, params={**base_params, "pagina": page})
            dados.extend(payload.get("dados", []))
        return dados

    async def fetch_deputados(self, itens: int = 100, all_pages: bool = False) -> list[dict]:
        params = {"itens": itens, "ordem": "ASC", "ordenarPor": "nome"}
        if all_pages:
            return await self._get_all_pages("/deputados", params=params, page_size=itens)
        payload = await self._get("/deputados", params=params)
        return payload.get("dados", [])

    async def fetch_deputados_historicos(self) -> list[dict]:
        payload = await self._get_download_json('/deputados/json/deputados.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_legislaturas(self) -> list[dict]:
        payload = await self._get_download_json('/legislaturas/json/legislaturas.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_orgaos_deputados_por_legislatura(self, legislatura: int) -> list[dict]:
        payload = await self._get_download_json(f'/orgaosDeputados/json/orgaosDeputados-L{legislatura}.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_proposicoes_por_ano_download(self, ano: int) -> list[dict]:
        payload = await self._get_download_json(f'/proposicoes/json/proposicoes-{ano}.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_proposicoes_autores_por_ano_download(self, ano: int) -> list[dict]:
        payload = await self._get_download_json(f'/proposicoesAutores/json/proposicoesAutores-{ano}.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_proposicoes_temas_por_ano_download(self, ano: int) -> list[dict]:
        payload = await self._get_download_json(f'/proposicoesTemas/json/proposicoesTemas-{ano}.json')
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            dados = payload.get('dados')
            if isinstance(dados, list):
                return dados
        return []

    async def fetch_deputado(self, deputado_id: int) -> dict:
        payload = await self._get(f"/deputados/{deputado_id}")
        return payload.get("dados", {})

    async def fetch_deputado_historico(self, deputado_id: int) -> list[dict]:
        payload = await self._get(f"/deputados/{deputado_id}/historico")
        return payload.get("dados", [])

    async def fetch_deputado_eventos(self, deputado_id: int) -> list[dict]:
        payload = await self._get(f"/deputados/{deputado_id}/eventos")
        return payload.get("dados", [])

    async def fetch_deputado_mandatos_externos(self, deputado_id: int) -> list[dict]:
        payload = await self._get(f"/deputados/{deputado_id}/mandatosExternos")
        return payload.get("dados", [])

    async def fetch_proposicoes(self, itens: int = 100, ano_inicio: int | None = None, ano_fim: int | None = None, all_pages: bool = False) -> list[dict]:
        params = {"itens": itens, "ordem": "DESC", "ordenarPor": "id"}
        if ano_inicio is not None:
            params["ano"] = ano_inicio if ano_inicio == ano_fim or ano_fim is None else None
        filtered_params = {key: value for key, value in params.items() if value is not None}
        if all_pages:
            return await self._get_all_pages("/proposicoes", params=filtered_params, page_size=itens)
        payload = await self._get("/proposicoes", params=filtered_params)
        return payload.get("dados", [])

    async def fetch_proposicao(self, proposicao_id: int) -> dict:
        payload = await self._get(f"/proposicoes/{proposicao_id}")
        return payload.get("dados", {})

    async def fetch_tramitacoes(self, proposicao_id: int, itens: int = 100, all_pages: bool = True) -> list[dict]:
        if all_pages:
            return await self._get_all_pages(f"/proposicoes/{proposicao_id}/tramitacoes", page_size=itens)
        payload = await self._get(f"/proposicoes/{proposicao_id}/tramitacoes", params={"itens": itens})
        return payload.get("dados", [])

    async def fetch_votacoes(self, proposicao_id: int, itens: int = 100, all_pages: bool = True) -> list[dict]:
        if all_pages:
            return await self._get_all_pages(f"/proposicoes/{proposicao_id}/votacoes", page_size=itens)
        payload = await self._get(f"/proposicoes/{proposicao_id}/votacoes", params={"itens": itens})
        return payload.get("dados", [])

    async def fetch_votacao_votos(self, votacao_id: str, itens: int = 100, all_pages: bool = True) -> list[dict]:
        if all_pages:
            return await self._get_all_pages(f"/votacoes/{votacao_id}/votos", page_size=itens)
        payload = await self._get(f"/votacoes/{votacao_id}/votos", params={"itens": itens})
        return payload.get("dados", [])


camara_client = CamaraClient()
