"""Read checked numeric model arrays one item at a time, with bounded item size."""

import json


def iter_json_array(path, max_item_chars=32 * 1024 * 1024, chunk_chars=1024 * 1024):
    if not 0 < chunk_chars <= max_item_chars:
        raise ValueError("invalid bounded reader configuration")
    decoder = json.JSONDecoder()
    with open(path, encoding="utf-8") as source:
        buffer, position, eof = "", 0, False

        def more():
            nonlocal buffer, position, eof
            buffer = buffer[position:]
            position = 0
            chunk = source.read(chunk_chars)
            eof = not chunk
            buffer += chunk
            if len(buffer) > max_item_chars:
                raise ValueError("model array item exceeds bounded reader limit")

        def token():
            nonlocal position
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
                if position < len(buffer):
                    return buffer[position]
                if eof:
                    raise ValueError("incomplete model JSON array")
                more()

        if token() != "[":
            raise ValueError("expected model JSON array")
        position += 1
        if token() != "]":
            while True:
                while True:
                    try:
                        value, end = decoder.raw_decode(buffer, position)
                        if end == len(buffer) and not eof:
                            more()
                            continue
                        if end < len(buffer) and buffer[end] not in " \t\r\n,]":
                            if not eof:
                                more()
                                continue
                            raise ValueError("invalid model array separator")
                        break
                    except json.JSONDecodeError:
                        if eof:
                            raise ValueError("invalid or incomplete model array item") from None
                        more()
                position = end
                yield value
                separator = token()
                position += 1
                if separator == "]":
                    break
                if separator != ",":
                    raise ValueError("invalid model array separator")
                if token() == "]":
                    raise ValueError("trailing comma in model JSON array")
        else:
            position += 1
        while True:
            if buffer[position:].strip():
                raise ValueError("trailing data after model JSON array")
            if eof:
                return
            position = len(buffer)
            more()
