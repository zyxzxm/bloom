# Fontes oficiais de hospedagem consultadas

- Render, deploy FastAPI: https://render.com/docs/deploy-fastapi — guia oficial de Web Service, comandos de build/start e URL de serviço.
- Render, persistent disks: https://render.com/docs/disks — discos persistentes disponíveis para serviços pagos; requer configurar o caminho de montagem e gravar os arquivos nesse diretório; disco é exclusivo de uma instância.
- Render, PostgreSQL: https://render.com/docs/postgresql-creating-connecting — criar banco no dashboard; URLs interna/externa e uso da URL interna na mesma região.
- Render, planos gratuitos: https://render.com/docs/free — web service Free suspende após 15 min sem tráfego e sistema de arquivos é efêmero; Postgres Free expira 30 dias após criação; a documentação diz que Free não é para produção.

Consulta feita em 2026-11-08. Reconfirmar os planos e limites diretamente nas páginas do fornecedor antes de produção.
