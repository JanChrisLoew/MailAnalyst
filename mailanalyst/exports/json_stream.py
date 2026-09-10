"""Incremental validation of a JSON records array."""

import json


def records(file):
    decoder = json.JSONDecoder()
    buffer, ended = "", False

    def refill():
        nonlocal buffer, ended
        part = file.read(65536)
        ended = not part
        buffer += part

    def whitespace():
        nonlocal buffer
        buffer = buffer.lstrip()
        while not buffer and not ended:
            refill()
            buffer = buffer.lstrip()

    whitespace()
    if not buffer.startswith("["):
        raise ValueError("Expected JSON array")
    buffer = buffer[1:]
    whitespace()
    if not buffer.startswith("]"):
        while True:
            while True:
                try:
                    row, end = decoder.raw_decode(buffer)
                    break
                except json.JSONDecodeError:
                    if ended:
                        raise ValueError("Incomplete JSON record")
                    refill()
            if not isinstance(row, dict):
                raise ValueError("Expected JSON record")
            yield row
            buffer = buffer[end:]
            whitespace()
            if buffer.startswith("]"):
                break
            if not buffer.startswith(","):
                raise ValueError("Expected JSON separator")
            buffer = buffer[1:]
            whitespace()
    buffer = buffer[1:]
    whitespace()
    if buffer:
        raise ValueError("Trailing JSON content")
