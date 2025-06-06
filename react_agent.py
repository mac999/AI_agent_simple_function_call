import argparse
import os
import json
import openai


def search(query: str) -> str:
    """Return dummy search results"""
    return f"Search results for '{query}'"


def calculator(expression: str) -> str:
    """Evaluate a math expression safely"""
    try:
        return str(eval(expression, {}, {}))
    except Exception as e:
        return f"error: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a math expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"],
            },
        },
    },
]

FUNCTION_MAP = {
    "search": search,
    "calculator": calculator,
}


def react_loop(messages):
    """Run the ReAct reasoning loop until a final answer is produced."""
    while True:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response["choices"][0]["message"]
        if msg.get("tool_calls"):
            messages.append(msg)
            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])
                result = FUNCTION_MAP[name](**args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                })
            continue
        messages.append(msg)
        return msg["content"]


def single_query(prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant using ReAct."},
        {"role": "user", "content": prompt},
    ]
    return react_loop(messages)


def chat_mode():
    messages = [{"role": "system", "content": "You are a helpful assistant using ReAct."}]
    print("Starting chat. Type 'exit' to quit.")
    while True:
        user = input("> ")
        if user.lower() in {"exit", "quit"}:
            break
        messages.append({"role": "user", "content": user})
        answer = react_loop(messages)
        print(answer)


def main():
    parser = argparse.ArgumentParser(description="Simple ReAct agent")
    parser.add_argument("prompt", nargs="?", help="Single prompt to run")
    parser.add_argument("-i", "--interactive", action="store_true", help="Chatbot mode")
    args = parser.parse_args()

    openai.api_key = os.environ.get("OPENAI_API_KEY")

    if args.interactive:
        chat_mode()
    elif args.prompt:
        print(single_query(args.prompt))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
