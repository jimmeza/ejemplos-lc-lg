async def my_async_function():
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain.chat_models import init_chat_model
    from langgraph.prebuilt import create_react_agent

    client = MultiServerMCPClient(
        {
            "postgresdb": {
                "url": "http://localhost:8000/sse/",
                "transport": "sse",
                #Puedes enviar encabezados, por ejemplo en caso tenga autorización 
                #Con este servidor MCP no hay autorización
                "headers": {
                    "Authorization": "Bearer TU_TOKEN",
                }
            }
        }
    )

    tools = await client.get_tools()
    llm = init_chat_model("google_genai:gemini-2.0-flash-lite", temperature=0)
    agent = create_react_agent(llm, tools)
    response = await agent.ainvoke(
        {"messages": "Muestrame la lista de tablas existentes en el esquema publico,"
                    "en formato CSV con solo el nombre de la tabla y el esquema."
        })

    for mensaje in response["messages"]:
        mensaje.pretty_print()

async def main():
    from dotenv import load_dotenv
    # Cargar las variables de entorno desde el archivo .env (aca debe ir el API Key del Proveedor del LLM)
    load_dotenv()

    await my_async_function()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())