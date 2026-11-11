.PHONY: install sample ingest transform export run site test lint docs clean

install:            ## Instala o pipeline (Python) e o site (Node)
	pip install -e ".[dev]"
	cd site && npm ci

sample:             ## Gera uma bronze de AMOSTRA (offline) para desenvolvimento
	python tests/fixtures/sample_bronze.py data/bronze

ingest:             ## Baixa dados novos das APIs (incremental)
	portal ingest

transform:          ## dbt build: modelos + testes de qualidade
	portal transform

export:             ## Gera os JSON consumidos pelo site
	portal export

run: ingest transform export   ## Pipeline completo

site:               ## Servidor de desenvolvimento do site
	cd site && npm run dev

docs:               ## Documentação do dbt (linhagem) em transform/target/static_index.html
	cd transform && dbt docs generate --static --profiles-dir .

test:               ## Testes unitários e ponta a ponta
	pytest -v

lint:
	ruff check src tests && ruff format --check src tests

clean:
	rm -rf data/warehouse transform/target site/dist site/public/data
