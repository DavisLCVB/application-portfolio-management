# MVP: Calibración del Reconciliador con un Conjunto Sintético Etiquetado

## Objetivo
Medir con datos (precisión, recall y F1) qué tan bien el pipeline de descubrimiento produce cada resultado —hipótesis anclada, candidato huérfano, conflicto y contrato multi-aplicación— y fijar los umbrales `MIN_LINK_SCORE`, `AMBIGUITY_MARGIN` y `REVIEW_THRESHOLD` a partir de esa medición, en lugar de suponerlos.

## Problema / por qué
El APM es un **caso académico sin datos reales** (decisión del usuario, 2026-10-11); "MEF" es solo un ejemplo ilustrativo. Los pesos y umbrales actuales (0.5 / 0.85 / 0.05) son supuestos. La arquitectura publicada (`docs/arquitectura/ia-agentes.md`) promete un *score* heurístico "calibrado antes de usarse". Sin datos reales, la forma defendible de cumplirlo es un conjunto sintético con verdad conocida (*ground truth*), que demuestra la **metodología** de calibración y gobierno, no el desempeño en una organización real.

## Decisiones aceptadas
1. Conjunto sintético **determinista** (semilla fija), generado por código y versionado; incluye la verdad conocida en un archivo de etiquetas.
2. Casos difíciles deliberados: coincidencia clara, alias divergente (`svc-pagos-v2` ↔ "Pasarela de Recaudación"), contrato multi-aplicación, repo/contrato huérfano, empate ambiguo (conflicto) y ruido (typos, abreviaturas, proveedores repetidos).
3. Separación calibración/evaluación (p. ej. 70 % / 30 %) para no sobreajustar los umbrales al mismo conjunto con que se reportan.
4. El acceso a fuentes reales (repos de proveedores, TDRs) se declara como **supuesto del caso académico** en la documentación.

## Alcance autorizado
- `mvp/` (generador, evaluador, tests, `src/config.py`, README).
- `docs/arquitectura/ia-agentes.md` (sección de calibración y supuesto académico).
- `odd/tasks/mvp-calibracion.md` (este archivo).
- Solo biblioteca estándar de Python; ejecución con `uv`.

## TDD
Aplica al código del MVP. Runner: `cd mvp && uv run python -m unittest discover -s tests -v`. Para la documentación: `cd website && npm test && npm run build`.

## Estrategia de entrega
Trunk-Based Development: un commit por tarea directamente en `main`; push a cargo del usuario. Pronóstico ~900 líneas en total (sobre el umbral orientativo de 400): se entrega por tareas como unidades de trabajo independientes; sin PRs.

## Tareas
- [x] C1 — Generador determinista del conjunto sintético (`mvp/src/synthetic.py` + salida en `mvp/datasets/sintetico/`): ~30 aplicaciones de catálogo, repos mínimos (`pom.xml`/`package.json`/`Dockerfile`), TDRs en Markdown y `labels.json` con la verdad esperada por evidencia (app(s) o huérfano o conflicto). Tests: misma semilla → mismo conjunto; todas las categorías presentes.
- [ ] C2 — Evaluador (`mvp/evaluate.py`): corre el pipeline sobre el conjunto, compara con `labels.json` y reporta precisión/recall/F1 por tipo de resultado y matriz de confusión (texto + JSON). Tests con un mini-conjunto de verdad conocida.
- [ ] C3 — Barrido de umbrales sobre la partición de calibración (`MIN_LINK_SCORE`, `AMBIGUITY_MARGIN`; `REVIEW_THRESHOLD` según tasa de nudges vs. errores), selección justificada y reporte sobre la partición de evaluación; actualizar `src/config.py` solo si la medición lo justifica.
- [ ] C4 — Documentar: sección "Calibración" en `docs/arquitectura/ia-agentes.md` con método, resultados y límites, y el supuesto académico sobre acceso a fuentes; actualizar `mvp/README.md`.

## Progreso
- Documento creado (2026-10-11). Antecedente: `odd/tasks/mvp-descubrimiento.md` T1–T12 completas (origin/main en `29d0b50`).
- C1 implementada (delegado, un escritor; pendiente de revisión y commit): `mvp/src/synthetic.py` + `mvp/datasets/sintetico/` (semilla 42: 30 apps, 36 evidencias en 7 categorías, partición 26/10); 66 tests OK; el pipeline corre sobre el conjunto con `--repos/--contracts/--catalog` sin cambios en `run_discovery.py`.

## Siguiente paso
C2 — Evaluador. Decidir con el usuario: criterio de acierto de `conflict` (conjunto exacto vs. inclusión) y si se corrige el bug de `_stack_similarity` ("java" coincide con "javascript") antes de medir.
