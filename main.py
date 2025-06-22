from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
from transformers import AutoTokenizer
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
import time
import logging
from telemetry import configure_telemetry, configure_logging
from typing import List, Literal
from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL   = "gpt-4.1-nano"

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatHistoryInput(BaseModel):
    messages: List[ChatMessage]

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


configure_telemetry()
configure_logging()

FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)
llm = pipeline("text2text-generation", model="google/flan-t5-base")
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")

@app.post("/generate")
async def generate_text(data: ChatHistoryInput):
    logger.info("Received chat history", extra={"turns": len(data.messages)})
    with tracer.start_as_current_span("generate_text") as span:
        start = time.time()
        result = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[msg.dict() for msg in data.messages],
                max_tokens=100,
            )
        duration = time.time() - start
        msg = result.choices[0].message.content
        usage = result.usage


        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        span.set_attribute("llm.latency_ms", int(duration * 1000))
        span.set_attribute("llm.tokens.input", input_tokens)
        span.set_attribute("llm.tokens.output", output_tokens)
        span.set_attribute("llm.tokens.total", total_tokens)
        span.set_attribute("llm.model", OPENAI_MODEL)
        span.set_attribute("llm.history.turns", len(data.messages))

        logger.info(
            "Response generated",
            extra={
                "latency_ms": int(duration * 1000),
                "response": msg,
                "tokens.input": input_tokens,
                "tokens.output": output_tokens,
                "tokens.total": total_tokens,
            }
        )
        
        return {"response": msg}
