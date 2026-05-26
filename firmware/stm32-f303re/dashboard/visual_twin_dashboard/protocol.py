from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .models import TelemetryFrame


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedLine:
    kind: str
    raw: str
    message: str = ""
    frame: Optional[TelemetryFrame] = None
    fields: Dict[str, str] = field(default_factory=dict)
    checksum_valid: bool = True


def nmea_checksum(payload: str) -> int:
    value = 0
    for char in payload:
        value ^= ord(char)
    return value & 0xFF


def split_nmea(line: str) -> tuple[str, bool]:
    text = line.strip()
    if not text.startswith("$"):
        raise ProtocolError("line does not start with '$'")

    body = text[1:]
    if "*" not in body:
        return body, True

    payload, checksum_text = body.rsplit("*", 1)
    if len(checksum_text) < 2:
        return payload, False

    try:
        received = int(checksum_text[:2], 16)
    except ValueError:
        return payload, False

    return payload, received == nmea_checksum(payload)


def parse_optional_float(text: str) -> Optional[float]:
    if text.upper() == "NAN":
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise ProtocolError(f"invalid float '{text}'") from exc


def parse_fault_bits(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise ProtocolError(f"invalid fault field '{text}'") from exc


def parse_telemetry(line: str, source: str = "serial") -> TelemetryFrame:
    payload, checksum_valid = split_nmea(line)
    parts = payload.split(",")
    if len(parts) != 9 or parts[0] != "T":
        raise ProtocolError("not a telemetry frame")

    try:
        ms = int(parts[1], 10)
        level = int(parts[8], 10)
    except ValueError as exc:
        raise ProtocolError("invalid integer field") from exc

    return TelemetryFrame(
        ms=ms,
        state=parts[2],
        mode=parts[3],
        fault_bits=parse_fault_bits(parts[4]),
        vdc1=parse_optional_float(parts[5]),
        vdc2=parse_optional_float(parts[6]),
        iout=parse_optional_float(parts[7]),
        level=level,
        checksum_valid=checksum_valid,
        source=source,
    )


def parse_status_fields(message: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for item in message.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def parse_line(line: str, source: str = "serial") -> ParsedLine:
    raw = line.rstrip("\r\n")
    if raw == "":
        return ParsedLine(kind="empty", raw=raw)
    if not raw.startswith("$"):
        return ParsedLine(kind="raw", raw=raw, message=raw)

    try:
        payload, checksum_valid = split_nmea(raw)
    except ProtocolError as exc:
        return ParsedLine(kind="protocol_error", raw=raw, message=str(exc), checksum_valid=False)

    prefix = payload.split(",", 1)[0]
    message = payload.split(",", 1)[1] if "," in payload else ""

    if prefix == "T":
        try:
            frame = parse_telemetry(raw, source=source)
        except ProtocolError as exc:
            return ParsedLine(
                kind="protocol_error",
                raw=raw,
                message=str(exc),
                checksum_valid=checksum_valid,
            )
        return ParsedLine(
            kind="telemetry",
            raw=raw,
            frame=frame,
            checksum_valid=frame.checksum_valid,
        )
    if prefix == "S":
        return ParsedLine(
            kind="status",
            raw=raw,
            message=message,
            fields=parse_status_fields(message),
            checksum_valid=checksum_valid,
        )
    if prefix == "A":
        return ParsedLine(kind="ack", raw=raw, message=message, checksum_valid=checksum_valid)
    if prefix == "E":
        return ParsedLine(kind="error", raw=raw, message=message, checksum_valid=checksum_valid)
    if prefix == "F":
        return ParsedLine(kind="fault", raw=raw, message=message, checksum_valid=checksum_valid)
    if prefix == "H":
        return ParsedLine(kind="help", raw=raw, message=message, checksum_valid=checksum_valid)
    if prefix == "C":
        return ParsedLine(
            kind="config",
            raw=raw,
            message=message,
            fields=parse_status_fields(message),
            checksum_valid=checksum_valid,
        )
    if prefix == "P":
        return ParsedLine(
            kind="protection",
            raw=raw,
            message=message,
            fields=parse_status_fields(message),
            checksum_valid=checksum_valid,
        )
    if prefix == "R":
        return ParsedLine(
            kind="adcraw",
            raw=raw,
            message=message,
            fields=parse_status_fields(message),
            checksum_valid=checksum_valid,
        )
    return ParsedLine(kind="raw", raw=raw, message=payload, checksum_valid=checksum_valid)


def make_telemetry_line(frame: TelemetryFrame, include_checksum: bool = True) -> str:
    def fmt(value: Optional[float]) -> str:
        return "NAN" if value is None else f"{value:.2f}"

    payload = (
        f"T,{frame.ms},{frame.state},{frame.mode},0x{frame.fault_bits:02X},"
        f"{fmt(frame.vdc1)},{fmt(frame.vdc2)},{fmt(frame.iout)},{frame.level}"
    )
    if include_checksum:
        return f"${payload}*{nmea_checksum(payload):02X}"
    return f"${payload}"

