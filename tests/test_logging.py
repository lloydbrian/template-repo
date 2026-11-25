import json
import logging

from template_sample_app.logging_config import JsonFormatter, request_id_var


def test_json_log_line_carries_request_id() -> None:
    token = request_id_var.set("req-42")
    try:
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello", None, None)
        line = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert line["msg"] == "hello"
    assert line["request_id"] == "req-42"
    assert line["level"] == "INFO"
