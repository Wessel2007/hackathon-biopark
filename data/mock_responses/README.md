# Mock Responses

Pasta reservada para **HTMLs salvos** de páginas de resultado de órgãos públicos.

## Uso no projeto atual

Os scrapers em `backend/app/services/scrapers/` tratam a maior parte dos órgãos com **simulação em código** (`fonte_consulta` com prefixo `SIMULADO:`). As consultas **reais** (Playwright) estão em `scraper.py` e nos módulos listados no [README.md](../../README.md#consultas-aos-órgãos).

Esta pasta **não é lida automaticamente** pelo sistema. Serve para:

- Evidências arquivadas pela equipe  
- Testes offline quando um portal estiver indisponível  
- Evolução futura (leitura de HTML com flag de ambiente)

## Uso futuro sugerido

1. Salve o HTML como `orgao_numero_protocolo.html`.
2. No scraper correspondente, leia o arquivo quando `MOCK_RESPONSES=1` (ou similar).
