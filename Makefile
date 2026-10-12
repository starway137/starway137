# Pipeline reproducible del proyecto de arqueología computacional.
PY ?= python3
P := 06_global-data-vault/pipelines

.PHONY: all validar cad features modelos prior informe codiseno test limpiar

all:            ## Pipeline completo (validación -> co-diseño)
	cd $(P) && $(PY) run_all.py

validar:
	cd $(P) && $(PY) validar.py

cad:
	cd $(P) && $(PY) construir_cad.py

features: cad
	cd $(P) && $(PY) extraer_features.py

modelos: features
	cd $(P) && $(PY) modelos_estadisticos.py

prior: modelos
	cd $(P) && $(PY) construir_prior.py

informe: prior
	cd $(P) && $(PY) informe.py

codiseno:       ## Ejemplo: make codiseno AREA=15000 MEZCLA="AW=0.5,SN=0.5"
	cd $(P) && $(PY) codiseno.py generar --area $(or $(AREA),12000) --mezcla "$(or $(MEZCLA),AW=0.6,SN=0.4)" \
		--nombre $(or $(NOMBRE),propuesta)

test:
	$(PY) -m unittest discover -s 06_global-data-vault/tests -v

limpiar:        ## Borra salidas generadas (se regeneran con make all)
	rm -rf */cad_parametric/salida 06_global-data-vault/codiseno/salidas
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
