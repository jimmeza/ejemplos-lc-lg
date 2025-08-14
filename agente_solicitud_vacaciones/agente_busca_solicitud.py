#Función para crear un prompt del sistema con el contexto de todo el procedimiento de registro de vacaciones,
#se usará para cualquier agente que trabaje en la automatización de este procedimiento,
#pero debe indicar su rol delimitado dentro de todo este procedimiento
def make_system_prompt(agent_role: str):
    from langchain_core.messages import SystemMessage
    return (
        SystemMessage(
        f"""
        Eres un asistente IA del área de Gestión Humana y debes ayudar a procesar las solicitudes de vacaciones.
        Asegurate que las respuestas sean en español.
        Asegurate de obtener la información necesaria de las herramientas disponibles.
        Asegurate de no llamar a las herramientas de forma paralela o dará error, y puedes usar la carpeta "./adjuntos" para guardar archivos.

        A continuación explico el procedimiento para procesar las solicitudes de vacaciones:

        Las solicitudes de vacaciones llegan como correo sin leer a la bandeja de entrada, con el asunto o el cuerpo relacionado a vacaciones o solicitud de vacaciones

        Las solicitudes de vacaciones son validas si se cumple lo siguiente (en caso contrario es invalida):
            1. El asunto o cuerpo estan relacionados con una solicitud de vacaciones
            2. Tiene un archivo adjunto con formato PDF, de una solicitud de vacaciones con una firma
            3. El nombre en el archivo de la solicitud debe corresponder al remitente del correo

        Procesar solicitudes de vacaciones validas:
            1. Registrar la solicitud de vacaciones
            2. Crear un borrador de correo de respuesta con un estilo informal, redacta el contenido dirigido al solicitante, indicando cuando se recibio su solicitud, y que su solicitud fue aceptada, con el id y fecha de registro de la solicitud creada, además del nombre del solicitante que está en el PDF adjunto.

        Procesar solicitudes de vacaciones invalidas:
            1. Crear un borrador de correo de respuesta con un estilo formal, redacta el contenido dirigido al solicitante, indicando cuando se recibio su solicitud, y el motivo por el que se rechazo su pedido

        {agent_role}
        """  
        )
        
    )

def build_vacation_request_agent():
    from validar_solicitud import validate_pdf
    #Esta herramienta se personalizo en el modulo gmail_get_message_with_attachments.py, 
    #ver comentarios en el código para mas detalle
    from gmail_get_message_with_attachments import GmailGetMessageWithAttachments
    from langchain_google_community import GmailToolkit
    from langchain_google_community.gmail.search import GmailSearch
    from langchain.chat_models import init_chat_model
    from langgraph.prebuilt import create_react_agent

    #Se crea el chat model a usar con buena capacidad agentica o Tool Calling
    llm = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)

    #Se instancia el Toolkit para GMail con el definiremos herramientas a usar
    toolkit = GmailToolkit()
    #Se crea la lista de herramientas necesarias para el agente
    vacation_request_tools = [
        GmailSearch(api_resource=toolkit.api_resource), #Herramienta para hacer la busqueda en la bandeja de correo
        GmailGetMessageWithAttachments(api_resource=toolkit.api_resource),  #Esta herramienta es personalizada y leera los correos
        validate_pdf, #Herramienta creada en el primer ejemplo para validar si un PDF es una solicitud de vacaciones válida
    ]

    #Se definen el aegente con su respecitvo LLM, Prompt y herramientas
    #Notese que en el Prompt tiene en su contexto todo el procedimiento pero se le indica un rol limitado
    vacation_request_agent = create_react_agent(
        llm, 
        tools=vacation_request_tools,
        prompt=make_system_prompt(
            "Tu rol es solo buscar las posibles solicitudes de vacaciones, e identificar si son validas o invalidas,"
            "aunque no tengan archivos adjuntos se deben considerar como invalidas y procesarlas."
            "Considerar que los archivos adjuntos de cada correo se guardan en una subcarpeta que se llama igual al id del correo, como [carpeta_de_trabajo]/[id_correo]."
            "Asegurate de que cada solicitud cumpla todas las condiciones para considerarla válida."
            "También mostrar la fecha y hora de recepción de su correo."
            "Trabajas con otro agente que se encargará de procesar las solicitudes que tu encuentres."
        ),
        name="vacation_request_agent"
    )
    return vacation_request_agent

#Esta es la lógica principal del ejemplo
def main(args=None):
    from dotenv import load_dotenv
    # Cargar las variables de entorno desde el archivo .env (aca debe ir el API Key del Proveedor del LLM)
    load_dotenv()

    from langchain_core.messages import HumanMessage

    #Creamos instancia del agente de solicitudes de vacaciones
    vacation_request_agent = build_vacation_request_agent()
    
    #Se ejecuta el agente en modo stream que envia las respuestas según las va generando
    events = vacation_request_agent.stream(
        {"messages": [
            HumanMessage("Buscar las posibles solicitudes de vacaciones de los ultimos 7 días"
                         )
        ]},
        {"recursion_limit": 100},
        stream_mode="values",
    )

    #Se va mostrando en la consola cada interacción o mensaje del agente
    #Se puede ver el detalle de lo que hace el agente al revisar la traza en LangSmith (incluyendo las llamdas a las herrameintas)
    for event in events:
        event["messages"][-1].pretty_print()

#Solo se llamará al método principal si se ejecuta este modulo directamente
if __name__ == "__main__":
    main()