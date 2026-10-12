"""
Parámetros configurables del pipeline de descubrimiento.

Los valores son heurísticos: deben recalibrarse contra un conjunto verificado
de aplicaciones conocidas antes de usarse en producción.
"""

# Score mínimo para vincular dos evidencias (o una evidencia con una aplicación
# del catálogo). Por debajo de este valor no hay vínculo: la evidencia se
# reporta como candidato huérfano. Debe ser menor que el umbral de revisión.
MIN_LINK_SCORE: float = 0.5
