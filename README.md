# Meu Políticos

Plataforma cívica focada no **processo legislativo brasileiro**, com:

- **Backend** em `FastAPI`
- **Mobile** em `React Native + Expo` (pós-MVP)
- **Web** em `React + Vite`
- **Consulta pública sem login**
- **Login opcional** para favoritos, acompanhamento e alertas (pós-MVP)
- **Suporte multilíngue** em `pt-BR`, `es` e `en`

## Posicionamento do MVP

- **Escopo do MVP:** Câmara dos Deputados
- **Público-alvo:** cidadãos, pesquisadores, jornalistas e comunidade cívica
- **Licenciamento pretendido:** GNU para favorecer uso, auditoria e contribuição pública
- **Login e mobile:** ficam para depois do MVP

## Estrutura

```text
backend/
mobile/
web/
DESIGN.md
plano-app-legislativo.md
```

## Design

O projeto usa um `DESIGN.md` próprio inspirado em referências de design editorial e interfaces confiáveis, adaptado para um contexto cívico brasileiro.

## Backend

Ver `backend/README.md`

## Infraestrutura

O projeto agora possui base para:

- `Docker Compose`
- `FastAPI` containerizado
- `PostgreSQL`
- `Redis`
- persistência com `SQLAlchemy`
- sincronização inicial de parlamentares da Câmara dos Deputados

## Mobile

Ver `mobile/README.md`

## Web

Ver `web/`

Funcionalidades iniciais da aplicação web:

- busca de leis e proposições aprovadas
- navegação para histórico parlamentar
- integração com os endpoints públicos do backend
- suporte a `pt-BR`, `es` e `en`

Para rodar localmente:

```bash
cd web
npm install
npm run dev
```

Configure `VITE_API_BASE_URL` se precisar apontar para outra URL do backend.

## Próximas fases

- expandir a ingestão real da Câmara para projetos, votações e tramitações com maior cobertura
- consolidar contrato público estável da API
- integrar dados do Senado Federal em fase posterior
- adicionar autenticação real com Google e Microsoft após o MVP
- conectar o mobile ao backend após o MVP
