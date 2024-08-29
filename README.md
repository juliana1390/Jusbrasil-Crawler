# Jusbrasil-Crawler
Desafio Técnico de estágio - Enterprise

O projeto trata-se de um crawler para fazer web scraping, através de uma API, para buscar dados processuais em todos os graus dos Tribunais de Justiça de Alagoas (TJAL) e do Ceará (TJCE).

TJAL
- [1º grau](https://www2.tjal.jus.br/cpopg/open.do)
- [2º grau](https://www2.tjal.jus.br/cposg5/open.do)

TJCE
- [1º grau](https://esaj.tjce.jus.br/cpopg/open.do)
- [2º grau](https://esaj.tjce.jus.br/cposg5/open.do)

---

## Pré-requisitos para rodar o projeto

Certifique-se de ter os seguintes softwares instalados no seu sistema:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Para verificar se estão instalados corretamente, execute os seguintes comandos:

```bash
docker --version
docker-compose --version
```

### Construir e Subir os Containers

Para construir as imagens Docker e iniciar os containers, execute o seguinte comando:

```bash
docker-compose up --build
```

Obs.: é possível alterar os processos no json de input
