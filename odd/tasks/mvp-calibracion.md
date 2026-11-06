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
- [x] C2 — Evaluador (`mvp/evaluate.py`): corre el pipeline sobre el conjunto, compara con `labels.json` y reporta precisión/recall/F1 por tipo de resultado y matriz de confusión (texto + JSON). Tests con un mini-conjunto de verdad conocida.
- [x] C3 — Barrido de umbrales sobre la partición de calibración (`MIN_LINK_SCORE`, `AMBIGUITY_MARGIN`; `REVIEW_THRESHOLD` según tasa de nudges vs. errores), selección justificada y reporte sobre la partición de evaluación; actualizar `src/config.py` solo si la medición lo justifica.
- [x] C4 — Documentar: sección "Calibración" en `docs/arquitectura/ia-agentes.md` con método, resultados y límites, y el supuesto académico sobre acceso a fuentes; actualizar `mvp/README.md`.

## Progreso
- Documento creado (2026-10-11). Antecedente: `odd/tasks/mvp-descubrimiento.md` T1–T12 completas (origin/main en `29d0b50`).
- C1 implementada (delegado, un escritor; pendiente de revisión y commit): `mvp/src/synthetic.py` + `mvp/datasets/sintetico/` (semilla 42: 30 apps, 36 evidencias en 7 categorías, partición 26/10); 66 tests OK; el pipeline corre sobre el conjunto con `--repos/--contracts/--catalog` sin cambios en `run_discovery.py`.
- C2 implementada y verificada (delegada; un escritor + verificación independiente + una corrección acotada de tests): `mvp/evaluate.py` (620 líneas), `mvp/tests/test_evaluate.py` (551), y `mvp/run_discovery.py` (+8/−1: parámetro opcional `min_link_score` reenviado a `SemanticReconciliator`, comportamiento por defecto intacto).
  - Mapeo de predicción por `evidence_id` con precedencia `conflict` → `multi_app` → `orphan` → `linked` → sin predicción; contratos por `doc_id`, repos por nombre; `multi_claim` resuelto por mayor confianza.
  - Reporte: matriz de confusión (filas = esperado, columnas = predicho + `missing`), P/R/F1 por clase, macro y micro, `app_id_accuracy` por conjunto exacto; JSON determinista (`mvp.evaluation.v1`, sin marcas de tiempo) en `mvp/output/evaluation_report.json`; CLI con `--split`, `--dataset`, `--json` y los tres umbrales.
  - Medición con umbrales actuales (`0.50 / 0.05 / 0.85`): partición de evaluación (n=10) exactitud 0.8000, macro F1 0.8167, `app_id_accuracy` 5/5; partición completa (n=36) exactitud 0.8333, macro F1 0.8187, `app_id_accuracy` 20/21. Cero etiquetas sin predicción.
  - Verificación: `uv run python -m unittest discover -s tests` → 81 tests OK; dos corridas producen JSON byte-idéntico (sha256 `ec2de841…6031b`); mutaciones probadas (transponer matriz, coaccionar `missing` a `orphan`, intercambiar `missing`/`unlabeled`) ahora fallan ≥1 test.
  - Discrepancias pipeline vs. etiqueta con los umbrales actuales (8 de 36): dos TDR esperados `linked` predichos `multi_app` (`TDR-2024-ORG-0405`, `TDR-2024-ORG-0740`), uno esperado `linked` predicho `orphan` (`TDR-2024-ORG-0754`), uno esperado `orphan` predicho `linked` (`TDR-2024-ORG-0897`), dos repos huérfanos predichos `linked`/`conflict` (`control-asistencia`, `gestion-citas`), un `app_ids` con app extra (`TDR-2024-ORG-0723`) y un conflicto con candidatas de más (`registro-visitas`). No se corrigió lógica del pipeline: es materia de C3.
  - Commit de C2: `0ed0f1c`.
- C3 implementada y verificada: `mvp/calibrate.py` (855 líneas) y `mvp/tests/test_calibrate.py` (308); commit `805cec7`.
  - Selección de `MIN_LINK_SCORE`/`AMBIGUITY_MARGIN` solo sobre calibración: maximizar exactitud micro → F1 macro → menos conflictos → mediana del plateau. `REVIEW_THRESHOLD`: menor umbral con error 0 y ≥1 auto-publicada; si no, minimizar errores y desempatar por menor carga de revisión.
  - Criterio de app_ids (decisión (a)): se reportan ambos —exacto y superconjunto— como métricas secundarias; la selección principal usa solo la clase de resultado, no los app_ids. Decisión (b) ya cerrada por el fix `b222d36` (stack por tokens, no subcadena).
  - Resultado sobre calibración (n=26): seleccionado (0.60/0.01) exactitud 0.9231 / F1 0.9106 / 4 conflictos, vs. actual (0.50/0.05) 0.8462 / 0.8194 / 5. PERO sobre la partición de evaluación reservada (n=10): seleccionado 0.7000 / F1 0.5985, peor que actual 0.8000 / 0.8167 — la mejora no generaliza (overfitting al corpus sintético minúsculo).
  - `REVIEW_THRESHOLD`: ningún umbral alcanza 0 errores (2 hipótesis incorrectas auto-publicadas persisten hasta 0.80); el script propone 0.70 con `zero_error=false`.
  - CONCLUSIÓN: la medición NO justifica cambiar `src/config.py`; se mantienen 0.50 / 0.05 / 0.85 como heurísticos pendientes de datos reales. Entregable de C3 = metodología de calibración, no un cambio de umbrales.
  - Verificación: 103 tests OK; reporte JSON determinista (byte-idéntico entre corridas).
- C4 completada: commit `474aa9c`.
  - `docs/arquitectura/ia-agentes.md`: sección "Calibración del score de confianza" (método, resultados, límites y supuesto académico de acceso a fuentes).
  - `mvp/README.md`: estructura del proyecto actualizada (`synthetic.py`, `evaluate.py`, `calibrate.py`, `connectors/`, `datasets/sintetico/`, tests de calibración/evaluación/conectores) y sección 9 "Calibración y evaluación (resultados)".
  - Verificación: `npm test` (2 OK) + `npm run build` (15 páginas) + 103 tests MVP OK.

## Estado
Todas las tareas de calibración (C1–C4) están completas. Quedan pendientes fuera de este track: el renombrado de la presentación (pptx) y el push de los commits a `origin/main`.
