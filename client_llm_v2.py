import os
import json
import asyncio
import logging

import openai                         # pip install openai>=1.14
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
)
log = logging.getLogger(__name__)

MCP_ENDPOINT = "http://localhost:8002/mcp"     # your server
openai.api_key = os.environ["OPENAI_API_KEY"]  # set in shell

async def list_tools(sess: ClientSession):
    """Ask server for available tools; return {name: meta_dict}."""
    tools_reply = await sess.list_tools()
    out = {t.name: t for t in tools_reply.tools}
    log.info("Server exposes tools: %s", ", ".join(out))
    return out


def to_openai_schema(tool_meta: dict) -> dict:
    """Convert MCP tool metadata to OpenAI function schema."""
    return {
        "type": "function", 
        "function": {
            "name": tool_meta.name,
            "description": tool_meta.description,
            "parameters": tool_meta.inputSchema
        }
    }

async def run_llm_session(sess: ClientSession, user_prompt: str):
    """
    Talk to the local LLM **on the client side**.
    The model decides whether to call a tool; if it does, we execute it
    through `sess.call_tool()` and feed the result back.
    """
    # ––– 1A.  discover tools & build schemas ––––––––––––––––––––––––
    tools = await list_tools(sess)
    schemas = [to_openai_schema(t) for t in tools.values()]

    # ––– 1B.  seed chat history –––––––––––––––––––––––––––––––––––––
    messages = [
        {
            "role": "system",
            "content": (
                "You are an IAM assistant.\n"
                "• If the user wants to echo a message → call hello with {message, kerberos_token}. "
                "All echo requests require a valid Kerberos token.\n"
                "• If the user asks about access or permissions (e.g., 'Can I access...', 'Do I have permission...') "
                "→ call check_permission with {permission_type}. "
                "For permission types with spaces, replace them with underscores (e.g., 'functional account' → 'functional_account').\n"
                "• If the user asks about account information → call get_account_info with {fid}.\n"
                "• If the user asks about service information → call get_service_info with {service_name}.\n\n"
                "Note: For testing Kerberos authentication, use 'mock-valid-token'."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]

    while True:
        # ––– 2.  hit OpenAI ––––––––––––––––––––––––––––––––––––––––
        log.info("Sending prompt to LLM …")
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=schemas,
            tool_choice="auto",
            temperature=0.1,
        )
        msg = completion.choices[0].message
        log.debug("OpenAI raw response: %s", msg)

        # ––– 3.  tool call? ––––––––––––––––––––––––––––––––––––––––
        if msg.tool_calls:
            for call in msg.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                log.info("LLM chose tool %s  args=%s", tool_name, args)

                # Call the tool on the MCP server
                result = await sess.call_tool(tool_name, args)
                log.info("→ Tool %s returned: %s", tool_name, result)

                # First, append the assistant's tool call
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": call.function.arguments
                        }
                    }]
                })
                
                # Then, append the tool's response
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": str(result)  # Ensure result is a string
                })
            continue

        # ––– 4.  plain-text answer –––––––––––––––––––––––––––––––––
        print("\nAssistant:", msg.content)
        break

async def access_mcp_tools():
    async with streamablehttp_client(MCP_ENDPOINT) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            print("\nIAM Assistant Ready! (Ctrl+C to exit)")
            print("Examples:")
            print("  - Say hello using Kerberos token mock-valid-token")
            print("  - Can I access functional account?")  # Updated to show permission check usage
            print("  - Do I have permission for service account?")  # Another permission example
            print("  - Get account info for a_foo")
            print("  - What are the details for service_a?")
            
            while True:
                try:
                    user_input = input("\n> ")
                    await run_llm_session(session, user_prompt=user_input)
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break

async def access_mcp_echo():
    # Connect to a streamable HTTP server
    async with streamablehttp_client(MCP_ENDPOINT) as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # Call a tool
            tool_result = await session.call_tool("echo", {"message": "hello", "kerberos_token": "valid-ticket"})
            print(f"Tool result: {tool_result}")

if __name__ == "__main__":
    #asyncio.run(access_mcp_echo())
    try:
        asyncio.run(access_mcp_tools())
    except KeyboardInterrupt:
        pass