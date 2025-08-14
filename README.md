# Ejemplos de LangChain y LangGraph


## Desde una aplicación IA simple hasta un multiagente con MCP

Aqui encontrarás el artículo y el caso de uso que se uso en los ejemplos [aqui](https://www.linkedin.com/pulse/solo-uses-ia-empieza-crear-tus-propias-aplicaciones-y-jim-meza-5xhxf/), donde con un solo caso de uso relativamente sencillo, se muestra cómo podemos implementar un multiagente IA, que usa herramientas personalizadas (para validar el contenido de un PDF), que usan integraciones con servicios externos (Gmail) o que consumen un servidor MCP(Postgress), todo esto con una aproximación incremental en cada ejemplo, partiendo desde una aplicación IA simple, hasta completar el multiagente IA que automatiza todo el procedimiento de solicitudes de vacaciones planteado en la publicación.

### Dependencias:
El repo cuenta con los archivos necesarios para instalar las dependencias con "pip", "poetry" o "UV", igualmente dejo la lista de dependencias usadas:

langchain python-dotenv langchain-google-genai langchain-openai fastapi "uvicorn[standard]" langchain_google_community langgraph langchain-google-community[gmail] langgraph-supervisor

Se uso Python versión 3.11.

### Configuración de variables de ambiente y de GMail:
Pueden tomar como base el archivo "ejemplo.env" y copiarlo con el nombre ".env", cambiando sus API Keys y demas variables que vayan a usar según los ejemplos a ejecutar.

Solo se necesita una API Key de OpenAI para ejecutar el modulo "api_validar_solicitud.py" del ejemplo 1, si no cuentas con una puedes cambiar el modelo usado en el modulo por uno de Gemini tal como en el archivo "validar_solicitud.py".

Para ver detalle de como configurar y crear API Key en LangSmith  ver: [https://docs.smith.langchain.com/observability](https://docs.smith.langchain.com/observability)

En caso no tengas una API Key de Gemini, puedes obtenerla usando una cuenta gratuita de Google siguiendo este [enlace](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys?hl=es-419&usertype=newuser)

Para poder acceder a un buzón de correo GMail, debes seguir las instrucciones para [Configurar Uso de API GMail en Google Cloud](https://developers.google.com/workspace/gmail/api/quickstart/python?hl=es-419), después de seguir las instrucciones y descargar el archivo credentials.json a la carpeta del proyecto, al ejecutar la aplicación te enviará a una página para dar permiso de acceso a la aplicación configurada y esto generará un archivo token.json en la carpeta del proyecto, lo que te dará acceso por una semana aproximadamente, cuando el token expire, borra el archivo token.json y vuelve a ejecutar la aplicación.

Si ya se ejecuto alguno de los multiagentes, se recomienda descartar los borradores de correo creados, para que el agente no tenga que evaluarlos, lo que aumenta el tiempo de computo y la cantidad de llamadas a los LLM (puede dar error por límite de uso excedido con cuenta de nivel gratuito).

Para la ejecución del [servidor MCP de Postgress](https://github.com/crystaldba/postgres-mcp) en Docker usar el comando:
docker run -p 8000:8000 -e "DATABASE_URI=postgresql://<usuario>:<password>@localhost:5432/<nombre BD>" crystaldba/postgres-mcp --access-mode=unrestricted --transport=sse

### Ejemplo 1: Aplicación IA simple que permita determinar si un archivo PDF es una solicitud de vacaciones válida.
Archivo: agente_solicitud_vacaciones/validar_solicitud.py

### Variante de Ejemplo 1: API REST que permita determinar si un archivo PDF es una solicitud de vacaciones válida.
Archivo: agente_solicitud_vacaciones/api_validar_solicitud.py

### Ejemplo 2: Agente IA simple que identificará los correos con solicitudes de vacaciones válida o inválidas.
Archivo: agente_solicitud_vacaciones/agente_busca_solicitud.py

### Ejemplo 3: Multiagente IA simple para el procesamiento de solicitudes de vacaciones.
Archivo: agente_solicitud_vacaciones/multiagente_solicitud_vacaciones.py

### Ejemplo 4: Multiagente IA simple para el procesamiento de solicitudes de vacaciones y consume servidor MCP.
Archivo: agente_solicitud_vacaciones/mcp_multiagente_solicitud_vacaciones.py

### Otros archivos:
agente_solicitud_vacaciones/gmail_get_message_with_attachments.py: Personalización de una clase de la bilbioteca de integraciones de LangChain ([GMailToolkit](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/tools/gmail/get_message.py))
