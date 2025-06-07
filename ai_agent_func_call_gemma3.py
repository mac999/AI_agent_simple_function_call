import gradio as gr
import ollama
import requests, json, os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

load_dotenv()
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

class SearchParameters(BaseModel):
	query: str = Field(..., description="Search term to look up")

class FunctionCall(BaseModel):
	name: str
	parameters: Dict[str, Any]

class SearchResult(BaseModel):
	title: str
	link: str
	snippet: str

	def to_string(self) -> str:
		return f"Title: {self.title}\nLink: {self.link}\nSnippet: {self.snippet}"

def google_search(query: str) -> SearchResult:
	"""Perform a Google search using Serper.dev API"""
	try:
		url = "https://google.serper.dev/search"
		payload = json.dumps({"q": query})
		headers = {
			'X-API-KEY': SERPER_API_KEY,
			'Content-Type': 'application/json'
		}
		
		response = requests.post(url, headers=headers, data=payload)
		response.raise_for_status()  # 잘못된 상태 코드에 대해 예외 발생
		
		results = response.json()
		
		if not results.get('organic'):
			raise ValueError("No search results found.")
			
		first_result = results['organic'][0]
		return SearchResult(
			title=first_result.get('title', 'No title'),
			link=first_result.get('link', 'No link'),
			snippet=first_result.get('snippet', 'No snippet available.')
		)
	except Exception as e:
		print(f"Search error: {str(e)}")
		raise

def parse_function_call(response: str) -> Optional[FunctionCall]:
	"""Parse the model's response to extract function calls"""
	try:
		# Clean the response and find JSON structure
		response = response.strip()
		start_idx = response.find('{')
		end_idx = response.rfind('}') + 1
		
		if start_idx == -1 or end_idx == 0:
			return None
			
		json_str = response[start_idx:end_idx]
		data = json.loads(json_str)
		return FunctionCall(**data)
	except Exception as e:
		print(f"Error parsing function call: {str(e)}")
		return None

# 프롬프트 시스템 메세지 정의
prompt_system_message = """You are an AI assistant with training data up to 2024. Answer questions directly when possible, and use search when necessary.

You will receive previous conversation messages as part of the input. Use these prior messages to maintain context and provide coherent, context-aware answers.

DECISION PROCESS:
1. For historical events before 2024:
   - Answer directly from your training data.
2. For events in 2024:
   - If you are certain, answer directly.
   - If you are unsure, use search.
3. For events after 2024 or current/recent information:
   - Always use search.
4. For timeless information (scientific facts, concepts, etc.):
   - Answer directly from your training data.

ALWAYS USE SEARCH if the question:
- Contains words like "current", "latest", "now", "present", "today", "recent"
- Asks about someone in a changing position (champion, president, CEO, etc.)
- Requests information that might have changed since 2024
- Is time-sensitive and does not specify a time period

FUNCTION CALL FORMAT:
When you need to search, respond WITH ONLY THE JSON OBJECT, no other text, no backticks:
{
	"name": "google_search",
	"parameters": {
		"query": "your search query"
	}
}

SEARCH FUNCTION:
{
	"name": "google_search",
	"description": "Search for real-time information",
	"parameters": {
		"type": "object",
		"properties": {
			"query": {
				"type": "string",
				"description": "Search term"
			}
		},
		"required": ["query"]
	}
}

WHEN ANSWERING BASED ON SEARCH RESULTS:
- Use ONLY facts found in the search results below.
- Do NOT add any dates or information not present in the search results.
- Do NOT make assumptions about timing or events.
- Quote dates exactly as they appear in the results.
- Keep your answer concise and factual.
"""

# 메시지 리스트를 생성하는 함수
def filter_memory(memory):
	"""assistant의 검색 안내 메시지를 memory에서 제외"""
	return [
		msg for msg in memory
		if not (
			msg["role"] == "assistant" and (
				msg["content"].startswith("Searching for:") or
				msg["content"].startswith("Searched for:")
			)
		)
	]

def build_messages(chat_history, user_input=None, prompt_system_message=prompt_system_message, N=6, search_result=None):
	"""
	최근 N개 메시지와 system 메시지를 합쳐 messages 리스트를 만듭니다.
	search_result가 있으면, user_input 대신 검색 결과 기반 프롬프트를 추가합니다.
	"""
	memory = chat_history[-N:] if len(chat_history) > N else chat_history[:-1]
	filtered_memory = filter_memory(memory)
	messages = [{"role": "system", "content": prompt_system_message}] + filtered_memory
	if search_result is not None:
		messages.append({
			"role": "user",
			"content": (
				"Refer to the following search result and provide a concise, factual answer based only on this information:\n"
				f"{search_result.to_string()}"
			)
		})
	elif user_input is not None:
		messages.append({"role": "user", "content": user_input})
	return messages

# Model name
MODEL_NAME = "gemma3"

def process_message(user_input, chat_history):
	"""Process user message and update chat history"""
	try:
		# 사용자 메시지를 기록에 추가
		chat_history.append({"role": "user", "content": user_input})
		search_info = None

		# 최근 N개 메시지만 memory에 포함 (예: 최근 6개)
		N = 6
		messages = build_messages(chat_history, user_input=user_input, N=N)

		# 모델로부터 응답 받기
		response = ollama.chat(
			model=MODEL_NAME,
			messages=messages		
		)
		
		model_response = response['message']['content']
		
		# 함수 호출로 응답을 파싱 시도
		function_call = parse_function_call(model_response)
		
		if function_call and function_call.name == "google_search":
			# 검색 파라미터 검증
			search_params = SearchParameters(**function_call.parameters)
			search_query = search_params.query
			
			# 검색 정보 기록에 추가
			search_info = f"Searching for: {search_query}"
			chat_history.append({"role": "assistant", "content": search_info})
			yield chat_history
			
			# 검색 실행
			search_result = google_search(search_query)
			
			# 검색 결과로 정보 업데이트
			search_info = f"Searched for: {search_query}\n\nResult:\n{search_result.to_string()}"
			chat_history[-1] = {"role": "assistant", "content": search_info}
			yield chat_history

			# 검색 결과 기반 메시지 생성
			messages = build_messages(chat_history, N=N, search_result=search_result)
	  
			# 검색 결과를 포함해 모델로부터 최종 응답 받기
			final_response = ollama.chat(
				model=MODEL_NAME,
				messages=messages
			)
			
			assistant_response = final_response['message']['content']
		else:
			# 함수 호출이 없으면 직접 응답 반환
			assistant_response = model_response
		
		# 최종 응답을 기록에 업데이트
		if search_info:
			chat_history.append({"role": "assistant", "content": f" Response:\n{assistant_response}"})
		else:
			chat_history.append({"role": "assistant", "content": assistant_response})
		
		yield chat_history
			
	except Exception as e:
		error_msg = f"An error occurred: {str(e)}"
		chat_history.append({"role": "assistant", "content": error_msg})
		yield chat_history

# Gradio 인터페이스 생성
with gr.Blocks(css="footer {visibility: hidden}") as demo:
	gr.Markdown("""
	# AI Agent using Google Gemma3
	

	""")
	
	chatbot = gr.Chatbot(
		height=700,
		show_label=False,
		avatar_images=(None, "https://api.dicebear.com/9.x/identicon/svg?seed=Mason"),
		type="messages"
	)
	
	with gr.Row():
		msg = gr.Textbox(
			scale=5,
			show_label=False,
			placeholder="Ask me anything...",
			container=False
		)
		submit_btn = gr.Button("Send", scale=1)
	
	with gr.Row():
		clear_btn = gr.Button("Clear Chat")
	

	# 이벤트 핸들러 설정
	msg.submit(
		process_message,
		[msg, chatbot],
		[chatbot],
	)
	
	submit_btn.click(
		process_message,
		[msg, chatbot],
		[chatbot],
	)
	
	clear_btn.click(
		lambda: [],
		None,
		chatbot,
		queue=False
	)
	
	# 메시지 전송 후 텍스트박스 비우기
	msg.submit(lambda: "", None, msg)
	submit_btn.click(lambda: "", None, msg)

if __name__ == "__main__":
	demo.launch(inbrowser=True, share=True) 