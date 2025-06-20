from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from dotenv import load_dotenv
import os
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
import logging

resource = Resource(attributes={
        SERVICE_NAME: "goutham-llm-fastapi" # replace with your desired service name
    })

def configure_telemetry():
    load_dotenv()
    signoz_key = os.getenv("SIGNOZ_INGESTION_KEY")


    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint="ingest.in.signoz.cloud:443", #replace with your ingestion endpoint depending on your region
        headers=(("signoz-ingestion-key", signoz_key),),
        insecure=False
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)


def configure_logging():
    load_dotenv()
    signoz_key = os.getenv("SIGNOZ_INGESTION_KEY")
    

    logger_provider = LoggerProvider(resource=resource)
    otlp_log_exporter = OTLPLogExporter(
        endpoint="ingest.in.signoz.cloud:443",
        headers=(("signoz-ingestion-key", signoz_key),),
        insecure=False
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    # Attach OpenTelemetry logging handler
    logging.setLoggerClass(logging.getLoggerClass())
    logging.basicConfig(level=logging.INFO)
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
