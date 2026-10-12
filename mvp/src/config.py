"""
Parámetros configurables del pipeline de descubrimiento.

Los valores son heurísticos: deben recalibrarse contra un conjunto verificado
de aplicaciones conocidas antes de usarse en producción.
"""

# Umbral único de revisión: una hipótesis con score heurístico mayor o igual
# queda como borrador publicable ("Draft"); por debajo requiere validación
# humana mediante micro-nudge. Lo comparten el reconciliador (Agente 3) y el
# generador de micro-nudges (Agente 4).
REVIEW_THRESHOLD: float = 0.85

# Score mínimo para vincular dos evidencias (o una evidencia con una aplicación
# del catálogo). Por debajo de este valor no hay vínculo: la evidencia se
# reporta como candidato huérfano. Debe ser menor que el umbral de revisión.
MIN_LINK_SCORE: float = 0.5

# Margen de conflicto: si el mejor y el segundo mejor score de una evidencia
# contra aplicaciones del catálogo superan el score mínimo de vinculación y
# difieren menos que este margen, la evidencia no discrimina entre ellas. Se
# reporta como conflicto en la cola de revisión humana y no se adjunta a
# ninguna hipótesis.
AMBIGUITY_MARGIN: float = 0.05
