from datetime import datetime
from typing import Dict
from agente_busca_solicitud import build_vacation_request_agent, make_system_prompt

def register_vacation_request(message_id: str, 
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
    #Acá deberiamos llamar a nuestro servicio que registra la solicitud de vacaciones
    #y hacemos que devuelva el número de solicitud registrado, por ahora es un Mock
    return {
        "solicitud_vacacion_id": "12345",
        "fecha_registro_solicitud": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def build_vacation_process_agent():
    from langchain_google_community import GmailToolkit
    from langchain_google_community.gmail.create_draft import GmailCreateDraft
    from langchain.chat_models import init_chat_model
    from langgraph.prebuilt import create_react_agent

    #Se crea el chat model a usar con buena capacidad agentica o Tool Calling
    llm = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=0)

    toolkit = GmailToolkit()
    #Se crea la lista de herramientas necesarias para cada agente
    vacation_process_tools = [
        GmailCreateDraft(api_resource=toolkit.api_resource),
        register_vacation_request,
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

#Esta es la lógica principal del ejemplo
def main(args=None):
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
    llm = init_chat_model("google_genai:gemini-2.0-flash-lite", temperature=0)

    #Se define el supervisor de los agentes, con su LLM, Prompt y lista de agentes
    supervisor = create_supervisor(
        agents=[vacation_request_agent, vacation_process_agent],
        model=llm,
        prompt=make_system_prompt(
            "Tu rol es coordinar con un agente encargado de identificar las solicitudes de vacaciones y "
            "un agente encargado de procesar las solicitudes de vacaciones. Asignales trabajo a ambos agentes sin pedir confirmaciones."
        ),
    ).compile()

    #Se envia instrucciones al supervisor, que asignara el trabajo a cada agente hasta que este completada la tarea
    events = supervisor.stream(
        {"messages": [
            HumanMessage("Procesar las posibles solicitudes de vacaciones de los ultimos 7 días.")
        ]},
        {"recursion_limit": 100},
        stream_mode="values",
    )

    #Se va mostrando en la consola cada interacción o mensaje del supervisor
    #Para ver el detalle de lo que hace cada agente se debe revisar la traza en LangSmith (incluyendo las llamadas a las herrameintas)
    for event in events:
        event["messages"][-1].pretty_print()

#Solo se llamará al método principal si se ejecuta este modulo directamente
if __name__ == "__main__":
    main()