# Simplifying LLM Function Calls for AI Agents

This project demonstrates a simplified approach to enable Large Language Models (LLMs) like ChatGPT or Llama to perform function calls effectively without relying on complex frameworks. The repository provides examples and tools to execute function calls with clear and predictable outcomes. In detail, refer to the below reference.
- [Effective and simplified LLM function call for AI agent development](https://medium.com/@laputa99999/effective-and-simplified-llm-function-call-for-ai-agent-development-6ccd6e44a191)
- [Gemma3-based Funcation Call Implement for AI Agent](https://daddynkidsmakers.blogspot.com/2025/06/gemma3-ollama-function-call.html)

<img src="https://github.com/mac999/AI_agent_simple_function_call/blob/main/gemma3.gif?raw=true" height="400"/>

## Features

- Minimal dependencies
- Simplified prompt design with function prototypes
- Python runtime execution using `exec`
- Easy-to-understand mechanism
- Simple ReAct implementation for AI Agent
- Gemma3 based function call web app example

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mac999/AI_agent_simple_function_call.git
   cd AI_agent_simple_function_call
   ```

2. Install the required dependencies:
   ```bash
   pip install langchain-core langchain-openai gradio ollama requests python-dotenv pydantic
   ```
   Additionally, ensure you have the following standard libraries (most are included by default with Python):

## Run Simple Function Call 

1. Define your function prototypes in Python.
2. Customize the prompts as needed.
3. Run the examples provided to understand the workflow.
```bash
python llm_func_call_for_ai_agent.py
```

Refer to the included examples in the repository to learn how to:

- Set up LLMs for function calls
- Use function prototypes for better results
- Execute generated Python code

## Run ReAct CLI

The `react_agent.py` script demonstrates a simple ReAct agent using the OpenAI API. Install the `openai` package and set the `OPENAI_API_KEY` environment variable before running.

### Single Query

```bash
python react_agent.py "What is 2+2?"
```

### Chatbot Mode

```bash
python react_agent.py -i
```

Type `exit` to quit the chat.

## Run Gemma3 based Function Call 
This source code implements the essential function call method for developing AI agents. It's contents of the Function Call practice using Ollama based on Gemma3 LLM (Large Language Model).
```bash
python ai_agent_func_call_gemma3.py
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License.

## Author

- **Taewook Kang**  
  Email: [laputa99999@gmail.com](mailto:laputa99999@gmail.com)
