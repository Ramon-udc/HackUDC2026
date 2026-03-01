# HackUDC2026

## Descripción

  Nuestro proyecto: PeixeAlert, se trata de un asistente inteligente de Telegram diseñado para los pescadores particulares de Galicia, el cual centraliza datos de MeteoGalicia para ofrecer estados del mar, clima y recomendaciones de pesca personalizadas según las condiciones actuales.

  Está caracterizado por poder seleccionar el puerto específico (Ferrol, Vigo...); dar detalles sobre el estado del mar (oleaje, viento...). generando sus respectivas tablas de datos, además de estimsar la calidad del día para la pesca; y por recomendar las especies presentes ese día según las condiciones anteriores.

## Tecnologías Utilizadas

Python: Lenguaje principal encargado de la lógica del bot, procesamiento de datos y comunicación con APIs.

Grafana cloud: Entorno de visualización avanzado donde se generan los gráficos temporales y los indicadores de aguja para el monitoreo de oleaje, viento y temperatura.

MeteoGalicia API: Fuente oficial de datos que proporciona información precisa sobre predicción numérica y mareas en la costa gallega.

## Características Principales

Interfaz Intuitiva: Menús basados en botones que eliminan la necesidad de memorizar comandos complejos.

Graficación clara: Integración de paneles visuales que muestran la evolución histórica de las olas y el viento.

Algoritmo de recomendación: Lógica programada que filtra especies según parámetros biológicos y meteorológicos.

## Instalación y Uso

1.- Asegúrarse de tener instalado Python 3.10+ y la librería python-telegram-bot.
2.- Configuración de API Keys, obteniendo previamente las credenciales necesarias (Telegram Token y MeteoGalicia API Key).
3.- En la ejecución, el código de Python extrae y procesa los datos de la API de MeteoGalicia. Estos datos se sincronizan con Grafana Cloud, donde se transforman automáticamente en representaciones visuales. De este modo, cuando el usuario consulta el bot, Python solicita a Grafana la generación de las gráficas y los indicadores de aguja, permitiendo que el pescador reciba una respuesta visualmente clara y profesional directamente en su chat de Telegram.

## Incidencias

Aunque en el estado actual todo funciona correctamente,  a lo largo del proyecto se nos presentaron algunos problemas como:

1.- Error inseperado al reanudar el proyecto durante la revisión final que acabó solucionándose solo.
2.- Dificultad para encontrar las ID de los puertos de Galicia.
3.- Problema al leer la API en el código definitivo.

## Contribución

Si deseas contribuir al proyecto, siéntete libre de hacer un fork y enviar un pull request con tus mejoras.

## Contacto

Para cualquier consulta o sugerencia, puedes contactarnos a través de [correo electrónico o redes sociales].

