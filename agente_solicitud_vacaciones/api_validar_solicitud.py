#Funcion para convertir un archivo local a Base64
def _get_base64_file(folder: str, file_name: str)-> str:
    """Obtiene el contenido de un archivo en base64"""
    import base64
    from pathlib import Path

    folder_path = Path(folder)
    file_path = folder_path / file_name

    with open(file_path, "rb") as f:
        pdf = base64.b64encode(f.read()).decode("utf-8")
    return pdf

#Funcion que usara un LLM para validar si un archivo es una solicitud de vacaciones válida
#Al momento de esta publicación, Langchain no soporta archivo PDF de forma dinámica (con plantillas), 
#por eso se crea un mensaje estático con el contenido de cada PDF, pero el texto si es dinámico
def validate_pdf(folder: str, file_name: str)-> str:
    """Devuelve  si el contenido del archivo pdf es una solicitud de vacaciones, 
    el nombre del solicitante y si el documento tiene una firma
    
    Args: 
        folder: carpeta del archivo a validar
        file_name: nombre del archivo a validar
    """
    if file_name[-4:].lower()!=".pdf":
        return "El archivo no es un PDF, no es una solicitud de vacaciones"
    
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    
    #Se crea el chat model usando un modelo que soporta recibir PDFs
    #En este ejemplo usaremos GPT4o mini
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    #Si deseas puedes usar Gemini, comentando la linea anterior y descomentando la siguiente
    #llm = init_chat_model("google_genai:gemini-2.0-flash-lite", temperature=0)

    #Obtengo el contenido del archivo en Base64 para poder enviarlo al API del LLM
    pdf_base64 = _get_base64_file(folder, file_name)

    #Se crea el prompt desde los mensajes y plantilla (ultimo mensaje con {query})
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage("""Asegurate que las respuestas sean en español."""),
            HumanMessage(
                [
                    {
                        "type": "file",
                        "source_type": "base64",
                        "data": pdf_base64,
                        "filename": file_name,
                        "mime_type": "application/pdf",
                    }                    
                ]),
            ("human", "{query}"),
        ]
    )
    
    #Se encadena el output del prompt con el input del llm
    chain = prompt | llm
    
    # Ejecuta la cadena 
    # Envio el PDF al LLM para que lo valide segun las instrucciones indicadas
    response = chain.invoke({"query":""""
                            ¿El contenido del documento es una solicitud de vacaciones?, 
                            si es así, obtener lo siguiente:
                            el nombre del solicitante 
                            si hay una firma
                            """})

    #Solo se devuleve un texto con la respuesta del pedido de validación del PDF (el formato es libre y lo redacta el LLM)
    return response.content


#Esta es la lógica principal del ejemplo que iniciara un servicio REST
def main(args=None):
    from dotenv import load_dotenv
    from fastapi import FastAPI
    # Cargar las variables de entorno desde el archivo .env (aca debe ir el API Key del Proveedor del LLM)
    load_dotenv()
    
    from pydantic import BaseModel
    
    #Se define entidad para los parametros del body para nuestro endpoint
    class dto_payload(BaseModel):
        folder: str = '../pdfs'
        file_name: str = 'vacaciones.pdf'
    
    #Se crea aplicacion de FastAPI
    app = FastAPI()

    #Defino el endpoint para la validacion del recurso solicitud de vacaciones con FastAPI
    @app.post("/vacation_request/validate")
    def validate_pdf_endpoint(dto: dto_payload)-> str:
        """Devuelve  si el contenido del archivo pdf es una solicitud de vacaciones, 
        el nombre del solicitante y si el documento tiene una firma
        
        Args: 
            folder: carpeta del archivo a validar
            file_name: nombre del archivo a validar
        """
        #Simplemente es una fachada y se redirige a la función que valida con un LLM
        return validate_pdf(dto.folder, dto.file_name)

    import uvicorn
    #Iniciamos el servidor web con uvicorn y la aplicacion de FastaAPI
    uvicorn.run(app, host="localhost", port=8000)
    #Pruebas desde la documentación OpenAPI: http://localhost:8000/docs

#Solo se llamará al método principal si se ejecuta este modulo directamente
if __name__ == "__main__":
    main()

