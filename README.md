# 1. Descripción general
Este es un código que resuelve el modelo TR20 con una varaible adicional para calibrar del método del Número de Curva (CN) del Servicio de Conservación de Recursos Naturales (SCS), con el fin de generar el hidrograma a interés, de hecho, se provee la calibración del modelo matemático a través del método de MonteCarlo.

Es importante mencionar, que este modelo TR20 modificado cobra bastante importancia, ya que se introduce una varirable adcional llamada caudal base, la cual será calibrada de la misma forma como se hace con las otras tres variables por defecto del modelo original.

En todo caso y, para que el código se ajuste a las necesidades que requiera cada persona, se recomienda clonar el código en cuestión y revisarlo minuciosamente.

# 2. Bibliotecas necesarias
pandas 2.2.3
numpy 2.2.0

# 3. Versión de Python utilizada
Python 3.12.4