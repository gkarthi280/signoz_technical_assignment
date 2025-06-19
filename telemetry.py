from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from dotenv import load_dotenv
import os

def configure_telemetry():
    load_dotenv()
    signoz_key = os.getenv("SIGNOZ_INGESTION_KEY")
    resource = Resource(attributes={
        SERVICE_NAME: "goutham-llm-fastapi"
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint="ingest.in.signoz.cloud:443",
        headers=(("signoz-ingestion-key", signoz_key),),
        insecure=False
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
