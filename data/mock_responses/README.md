# Mock Responses

Esta pasta é reservada para **HTMLs salvos** de consultas reais nos sites dos órgãos públicos.

## Uso atual do projeto

Os scrapers em `backend/app/services/scrapers/` hoje usam **simulação em código** (respostas mockadas com `fonte_consulta` prefixada por `SIMULADO:`). Apenas o **Cartório de Imóveis (PR)** é consultado de forma real via Playwright (`backend/app/services/scraper.py`).

Esta pasta **não é lida automaticamente** pelos scrapers atuais. Ela serve para:

- Desenvolvimento futuro com leitura de HTML offline
- Testes quando um site público estiver indisponível
- Evidências arquivadas da equipe

## Como usar no futuro

1. Salve o HTML da página de resultado como `orgao_protocolo.html`.
2. Adapte o scraper correspondente para ler o arquivo quando `MOCK_RESPONSES=1` ou similar.

Consulte o [README.md](../../README.md#consultas-aos-órgãos) para a lista de órgãos reais vs. simulados.
