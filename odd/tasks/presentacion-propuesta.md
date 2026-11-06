# Propuesta de presentación — «APM con IA Agéntica»

**Base:** `GobIA_TF_Informe_Final.docx` (20 páginas).
**Formato del curso:** 25–30 min por equipo (20 de exposición + 8 de preguntas), máximo 20 diapositivas, evaluación individual.
**Criterio de diseño:** una idea por diapositiva, tres bullets como máximo, visual a la derecha, cifras solo donde suman. No se lee la diapositiva: se usa como ancla.

---

## 1. Secciones principales del documento

| # | Sección | Páginas | Función en la narrativa |
|---|---|---|---|
| — | Resumen ejecutivo | 3 | Tesis y estado en una página |
| 1 | Introducción y contexto | 3–5 | Problema, causas, consecuencias, caso, procesos y estado |
| 2 | Inventario y alineamiento OCDE | 6–7 | Qué capacidades de IA existen y cómo se alinean con los principios |
| 3 | Riesgos y aceptabilidad | 8–9 | 10 dimensiones éticas, 5 de impacto, criterios A / A+C / NA |
| 4 | Gobernanza de proyectos y proveedores | 10–13 | Checklist, agentes, datos, KPI y mecanismo de detención |
| 5 | Lineamientos operativos | 14–15 | Usos permitidos, restringidos y no permitidos; IA generativa |
| 6 | Modelo institucional | 15–16 | Roles, integración normativa y hoja de ruta adaptable |
| 7 | Conclusiones y próximos pasos | 17–18 | Mensajes de cierre, limitaciones y plan de evaluación |
| — | Glosario y bibliografía | 19–20 | Referencia |

---

## 2. Enfoque narrativo

**Hilo:** «El catálogo no falla por falta de análisis, sino porque mantenerlo cuesta más de lo que vale. La IA ayuda si ataca la captura y la identidad; y eso solo se sostiene si se gobierna.»

La presentación sigue ese hilo en cuatro actos:

1. **El problema** (diapositivas 2–4): síntoma, causas, consecuencias.
2. **La solución** (5–9): cuatro agentes, evidencia, reconciliación y valor para el equipo.
3. **El gobierno** (10–13): regla de decisión, riesgos, datos, agentes.
4. **La realidad** (14–18): qué se midió y qué no, hoja de ruta, adopción, roles y cierre.

---

## 3. Propuesta de diapositivas (18 principales + 2 de respaldo)

| # | Título | Contenido (máx. 3 bullets) | Visual | Tiempo |
|---|---|---|---|---|
| 1 | **Portada** | Título, autor, curso, fecha | Portada del portal o captura del índice | 0:30 |
| 2 | **El problema** | «El catálogo llega tarde»; el costo de mantenerlo supera su valor; no falta un repositorio, falta costo de captura | Línea de tiempo: la ficha envejece mientras el portafolio cambia | 1:30 |
| 3 | **Por qué pasa** | Incentivos mal alineados; dispersión sin árbitro; identidad sin dueño (+ presupuesto) | Cuatro iconos con una frase cada uno | 1:30 |
| 4 | **Qué se pierde** | Shadow IT; decisiones sobre datos incompletos; el equipo deja de confiar en el catálogo | Círculo vicioso: dato viejo → desconfianza → menos reporte | 1:00 |
| 5 | **La tesis** | La IA deja de ser «bombero downstream»; se pone en el descubrimiento; cuatro agentes | Dos capas: upstream (descubrir) y downstream (consumir) | 1:00 |
| 6 | **Cómo descubre** | Agente 1 lee repos y CI/CD con parsers; Agente 2 lee contratos y TDR con LLM; cada dato nace con evidencia | Pipeline simplificado de la arquitectura | 1:30 |
| 7 | **Cómo concilia** | Score 0–1; umbral único; «Requiere Verificación», huérfanos y conflictos a revisión humana | Matriz score/umbral con zona de revisión | 1:30 |
| 8 | **Cómo pregunta** | Micro-nudges de un clic; notificaciones por evento; solo lo que las reglas no resuelven | Notificación + ficha + respuesta en un clic | 1:00 |
| 9 | **Qué devuelve al equipo** | Consulta abierta a todo TI; cada dueño ve su ficha, CVE y EOL; reportar deja de ser una carga | Ficha con hallazgos y aviso al dueño | 1:00 |
| 10 | **La regla de gobierno** | La IA propone con evidencia, la persona dispone; publicación automática solo de atributos técnicos deterministas; todo lo demás requiere aprobación | Dos carriles: automático vs. aprobado | 1:30 |
| 11 | **Riesgos OCDE** | Diez dimensiones, cinco principios; los tres riesgos críticos: vinculación, datos personales, fatiga | Mapa de calor de riesgos | 1:30 |
| 12 | **Datos y roles** | Cuatro niveles de clasificación; seudonimización; lectura, edición, aprobación y descarga por rol | Tabla simplificada de 4 niveles | 1:00 |
| 13 | **Gobernanza de agentes** | Permisos de mínimo privilegio; bitácora; HITL; detención en tres niveles | Interruptor de tres posiciones | 1:00 |
| 14 | **¿Funciona?** | 36 casos de prueba; la calibración no concluye; evidencia de diseño, no de operación | Semáforo: probado / no probado | 1:30 |
| 15 | **Hoja de ruta** | Cuatro hitos con compuertas; condiciones de aplicabilidad; perfiles de entrada | Cuatro columnas con compuertas | 1:30 |
| 16 | **Adopción** | Política de Dirección; consulta y notificaciones; carga de revisión y señales de resistencia | Volante: reportar → usar → confiar | 1:00 |
| 17 | **Modelo institucional** | Arquitectura TI dueña; Gobierno de Arquitectura aprueba; Dirección patrocina; Seguridad y Auditoría controlan | Organigrama de cinco roles | 1:00 |
| 18 | **Cierre** | Tres mensajes: el cuello de botella es captura e identidad; la IA se gobierna con evidencia y compuertas; la adopción es política, no solo técnica | Tres frases grandes | 1:00 |
| B1 | **Respaldo: calibración** | 26/10, métricas, intervalos, sobreajuste | Tabla compacta | — |
| B2 | **Respaldo: proveedor** | Cuatro capacidades técnicas + tres contractuales | Checklist | — |

**Total:** 18 + 2 de respaldo = 20. Los respaldos no se exponen; se abren en preguntas.

---

## 4. Guion de tiempos (20 minutos)

| Bloque | Diapositivas | Tiempo |
|---|---|---|
| Apertura y problema | 1–4 | 4:30 |
| Solución | 5–9 | 5:30 |
| Gobierno | 10–13 | 5:00 |
| Realidad y cierre | 14–18 | 5:00 |
| **Total** | | **20:00** |

Deja 8 minutos para preguntas. Las dos de respaldo cubren las más probables: «¿cómo midieron?» y «¿qué pasa si ya tengo proveedor?».

---

## 5. Mapa a la rúbrica de la exposición

| Criterio | Dónde se cubre |
|---|---|
| **P1 · Dominio del contenido** | Diapositivas 5–13; en preguntas, respaldos B1 y B2 |
| **P2 · Claridad y estructura** | Los cuatro actos y los títulos de sección; una idea por diapositiva |
| **P3 · Respuesta a preguntas** | Respaldos y las cifras precisas de B1 |
| **P4 · Conexión con el contexto institucional** | Diapositiva 17 y la mención, si preguntan, de qué cambia en una entidad pública (contratación, control, transparencia) |
| **P5 · Contribución visible** | Diapositiva 18 y el cierre con el portal y el prototipo como evidencia propia |

---

## 6. Riesgos y cómo cubrirlos

1. **La rúbrica pide contexto MEF y el informe no lo incluye.** No lo pongas en las diapositivas. Si preguntan, responde en la diapositiva 17: «en una entidad pública cambian la contratación, las instancias de aprobación y las reglas de publicación; el resto del modelo se mantiene». Así cubres la conexión sin convertir al MEF en cliente.
2. **No sobrevender la calibración.** La diapositiva 14 dice explícitamente «no concluyente». Eso suma credibilidad; si te preguntan por números, abre B1.
3. **Tecnicismos.** Cada agente se presenta con una frase y un verbo: lee, extrae, concilia, pregunta. No nombres el score sin explicar qué decide.
4. **Tiempo.** Si vas justo, recorta la 8 o la 16; nunca la 2, la 10 o la 14.

---

## 7. Estilo visual sugerido

- Fondo blanco, azul marino para títulos, un color de acento (ámbar) para lo que requiere decisión humana.
- Una captura o diagrama por diapositiva; nada de párrafos.
- Números grandes solo en las diapositivas 14 y 15.
- Pie: «APM con IA Agéntica - Davis Cartagena» y número de diapositiva.

---

## 8. Siguiente paso

Si te sirve esta estructura, la construyo como `.pptx` de 20 diapositivas con el mismo estilo visual del informe (Google Sans, azul marino, tablas limpias) y notas del expositor por diapositiva.

---

## 5. Rediseño alineado al informe final (2026-11-06)

- [x] Identidad del informe: Google Sans, azul `14324B`, texto `1A1A1A`, gris `5A6670`, rellenos `F6F8FA`/`E8EEF4`.
- [x] Portada blanca con los metadatos del informe (Autor, Docente, Caso, Fecha).
- [x] Cuerpo ≥ 14 pt, visuales a todo el alto útil, viñetas redundantes reemplazadas (7, 8, 16).
- [x] Pie con la sección del informe que respalda cada diapositiva (`Informe · 1.1`, …).
- [x] Organigrama (17) con conectores alineados; barra de score (7) con umbral rotulado.
- Verificación: `validate.py` PASSED; render revisado diapositiva por diapositiva.
- Riesgo: Google Sans debe estar instalada en el equipo de exposición; si no, exportar a PDF.

## 6. Estilo de apm-agents (2026-11-06)

- [x] Paleta y tipografía de `docs/presentaciones/apm-agents.pptx`: Calibri, petróleo `0B3C49`, teal `127C86`, coral `C4533A`, amarillo `F2A900`, lienzo `EEF3F4`.
- [x] Tarjetas blancas con sombra suave; iconos en círculos (react-icons + sharp en `.deck/`).
- [x] Portada oscura con motivo de hub; subtítulo bajo cada título en lugar del kicker de sección.
- [x] Se mantienen los metadatos del informe y la referencia «Informe · §» en el pie.
- Verificación: `validate.py` PASSED; render revisado diapositiva por diapositiva.

## 7. Diagramas y variedad de layout (2026-11-06)

Ruta: inline (un solo archivo, `build-deck.js`).

- [x] D1 · Causas y consecuencias en un diagrama (fusiona las antiguas 3 y 4).
- [x] D2 · Arquitectura de la solución: pipeline de cinco etapas + barra del catálogo gobernado (reemplaza la tesis 5).
- [x] D3 · Riesgo → mitigación por diseño, con los cinco principios OCDE como chips.
- [x] D4 · Fila de cifras grandes en «Qué se midió».
- [x] D5 · Ciclo de adopción dibujado + tres palancas.
- [x] D6 · Regla de gobierno como dos carriles con la persona como compuerta.
- [x] D7 · Iconos en datos, detención y roles; frases finales solo donde son el mensaje.
- [x] D8 · «Gracias» en diapositiva propia con el hub.
- Verificación: `validate.py` PASSED; render revisado diapositiva por diapositiva. Total: 18 + 2 de respaldo (las antiguas 3 y 4 se fusionaron, la tesis se absorbió en la arquitectura y «Gracias» quedó aparte).
