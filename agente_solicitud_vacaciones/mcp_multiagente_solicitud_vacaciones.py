from datetime import datetime
from typing import Dict
from agente_busca_solicitud import build_vacation_request_agent, make_system_prompt
from langchain_core.tools import tool

#Para poder manejar el cliente MCP, de funcion debe ser asincrona.
#Esta función va a usar un agente IA para crear la tabla "solicitud_vacaciones" (si no existe)
#y registrar la solicitud en dicha tabla, para esto se usará un servidor MCP para Postgress
# https://github.com/crystaldba/postgres-mcp , se ejecutará con Docker (ver detalles en el repo)
async def register_vacation_request(message_id: str, 
                              nombre_solicitante: str, 
                              fecha_solicitud:datetime
                              )->Dict:
    """Registra la solicitud de vacaciones y devuelve los datos principales de la solicitud, como su id

    Args:
        message_id (str): ID del correo con la solicitud de vacaciones
        nombre_solicitante (str): Nombre del solicitante
        fecha_solicitud (datetime): Fecha de envío de correo de solicitud

    Returns:
        Dict: id de solicitud y fecha de registro de solicitud
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain.chat_models import init_chat_model
    from langgraph.prebuilt import create_react_agent

    #Se instancia el cliente del servidor MCP de Postgress que estoy ejecutando con Docker
    client = MultiServerMCPClient(
        {
            "postgresdb": {
                "url": "http://localhost:8000/sse/",
                "transport": "sse", #Este servidor soporta http por SSE
                #Puedes enviar encabezados, por ejemplo en caso tenga autorización 
                #Con este servidor MCP no hay autorización
                "headers": {
                    "Authorization": "Bearer TU_TOKEN",
                }
            }
        }
    )

    #Se instancia las herramientas configuradas en el cliente MCP (pueden ser varias) 
    tools = await client.get_tools()
    #Se crea el chat model a usar con buena capacidad agentica o Tool Calling
    llm = init_chat_model("google_genai:gemini-2.5-flash", temperature=0)
    #Se definen el aegente con su respecitvo LLM y herramientas (no necesita que se defina un prompt)
    agent = create_react_agent(llm, tools)
    #Se ejecuta el agente con las instrucciones necesarias para crear la tabla y el registro
    response = await agent.ainvoke(
        {"messages": f"""Si no existe la tabla solicitud_vacaciones, crearla con los siguientes campos:
         solicitud_vacacion_id (identificador entero autonumerico),
         fecha_registro_solicitud (formato de fecha y hora, se guarda la fecha y hora en el momento de crear el registro),
         message_id (texto de 36 caracteres como máximo),
         nombre_solicitante (texto de 100 caracteres como máximo),
         fecha_solicitud (formato de fecha y hora, es enviado por el usuario).
         
         Luego insertar una solicitud de vacaciones con estos datos:
         message_id = {message_id},
         nombre_solicitante = {nombre_solicitante},
         fecha_solicitud = {fecha_solicitud}
         
        Finalmente, en formato json, devolver del registro creado, solicitud_vacacion_id y fecha_registro_solicitud""",
        }, 
    )
    #Se devuelve el contenido del ultimo mensaje que debe ser un JSON (tambien se puede definir una estructura de salida)
    return response["messages"][-1].content
    
def build_vacation_process_agent():
    from langchain_google_community import GmailToolkit
    from langchain_google_community.gmail.create_draft import GmailCreateDraft
    from langchain.chat_models import init_chat_model
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import StructuredTool

    llm = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=0)

    toolkit = GmailToolkit()
    #Se crea la lista de herramientas necesarias para cada agente
    gmail_draft = GmailCreateDraft(api_resource=toolkit.api_resource)
    vacation_process_tools = [
        gmail_draft,
        StructuredTool.from_function(coroutine=register_vacation_request), #Esta Tool es asincrona y se debe usar StructuredTool
    ]

    #Se definen el aegente con su respecitvo LLM, Prompt y herramientas
    #Notese que en el Prompt tiene en su contexto todo el procedimiento pero se le indica un rol limitado
    vacation_process_agent = create_react_agent(
        llm,
        tools=vacation_process_tools,
        prompt=make_system_prompt(
            "Tu rol es solo procesar las solicitudes de vacaciones validas o invalidas,"
            "trabajas con otro agente que te entregará las solicitudes que tu debes procesar."
            "Asegurate de realizar la tareas indicadas el el procesamiento de solicitudes validas o invalidas."
        ),
        name="vacation_process_agent"
    )
    return vacation_process_agent

#Esta es la lógica principal del ejemplo y debe ser asincrona
async def main(args=None):
    from dotenv import load_dotenv
    # Cargar las variables de entorno desde el archivo .env (aca debe ir el API Key del Proveedor del LLM)
    load_dotenv()

    from langchain_core.messages import HumanMessage
    from langgraph_supervisor import create_supervisor
    from langchain.chat_models import init_chat_model

    #Creamos instancia de los agentes IA que van a trabajar con el supervisor
    vacation_request_agent = build_vacation_request_agent()
    vacation_process_agent = build_vacation_process_agent()
    
    #Se crea el chat model a usar con buena capacidad agentica o Tool Calling
    llm = init_chat_model("google_genai:gemini-2.5-pro", temperature=0)

    #Se define el supervisor de los agentes, con su LLM, Prompt y lista de agentes
    supervisor = create_supervisor(
        agents=[vacation_request_agent, vacation_process_agent],
        model=llm,
        prompt=make_system_prompt(
            "Tu rol es coordinar con un agente encargado de identificar las solicitudes de vacaciones y "
            "un agente encargado de procesar las solicitudes de vacaciones. Asignales trabajo a ambos agentes sin pedir confirmaciones."
        ),
        supervisor_name="vacation_supervisor"
    ).compile()

    #Se envia instrucciones al supervisor, que asignara el trabajo a cada agente hasta que este completada la tarea
    #se ejecuta de forma asincrona con la funcion astream
    response = supervisor.astream(
        {"messages": [
            HumanMessage("Procesar las posibles solicitudes de vacaciones de los ultimos 7 días.")
        ]},
        {"recursion_limit": 100},
        stream_mode="values",
    )

    #Se va mostrando en la consola cada interacción o mensaje del supervisor
    #Para ver el detalle de lo que hace cada agente se debe revisar la traza en LangSmith (incluyendo las llamadas a las herrameintas)
    async for mensaje in response:
        mensaje["messages"][-1].pretty_print()

#Solo se llamará al método principal si se ejecuta este modulo directamente
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())