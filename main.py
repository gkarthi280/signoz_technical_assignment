from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
from transformers import AutoTokenizer
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
import time
from telemetry import configure_telemetry

class PromptInput(BaseModel):
    prompt: str

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

FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)
llm = pipeline("text2text-generation", model="google/flan-t5-base")
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")

@app.post("/generate")
async def generate_text(data: PromptInput):
    with tracer.start_as_current_span("generate_text") as span:
        start = time.time()
        result = llm(data.prompt, max_new_tokens=100)[0]["generated_text"]
        duration = time.time() - start

        input_tokens = len(tokenizer.encode(data.prompt))
        output_tokens = len(tokenizer.encode(result))
        total_tokens = input_tokens + output_tokens

        span.set_attribute("llm.prompt.length", len(data.prompt))
        span.set_attribute("llm.response.length", len(result))
        span.set_attribute("llm.latency_ms", int(duration * 1000))

        span.set_attribute("llm.tokens.input", input_tokens)
        span.set_attribute("llm.tokens.output", output_tokens)
        span.set_attribute("llm.tokens.total", total_tokens)

        return {"response": result}
