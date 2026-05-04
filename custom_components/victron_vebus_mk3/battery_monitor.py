from __future__ import annotations

import asyncio
from typing import Any


BATTERY_SOC_VARIABLE_ID = 13


def register_battery_soc_variable(mk3: Any) -> None:
    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return

    variable_info = getattr(driver, "_variable_info", None)
    variable_id_queue = getattr(driver, "_variable_id_queue", None)
    if variable_info is None or variable_id_queue is None:
        return

    if (
        BATTERY_SOC_VARIABLE_ID not in variable_info
        and BATTERY_SOC_VARIABLE_ID not in variable_id_queue
    ):
        variable_id_queue.append(BATTERY_SOC_VARIABLE_ID)


async def read_battery_soc(mk3: Any) -> float | None:
    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    variable_info = getattr(driver, "_variable_info", None)
    if variable_info is None or BATTERY_SOC_VARIABLE_ID not in variable_info:
        return None

    value = await _read_ram_variable(
        driver,
        BATTERY_SOC_VARIABLE_ID,
        variable_info[BATTERY_SOC_VARIABLE_ID],
    )
    return _normalize_battery_soc(value, variable_info[BATTERY_SOC_VARIABLE_ID])


def _normalize_battery_soc(value: float | None, parser: Any) -> float | None:
    if value is None:
        return None

    scale = getattr(parser, "_scale", None)
    if isinstance(scale, (int, float)) and 0 < scale < 1 and 0 <= value <= 1:
        return value * 100

    return value


async def _read_ram_variable(driver: Any, variable_id: int, parser: Any) -> float | None:
    completed = asyncio.Event()
    result: dict[str, float | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            if len(msg) < 5:
                raise ValueError(f"Unexpected RAM variable response length: {len(msg)}")

            code = msg[2]
            if code == 0x90:
                result["value"] = None
                return
            if code != 0x85:
                raise ValueError(f"Unexpected RAM variable response code: {code:#x}")

            result["value"] = parser.parse(msg[3:5])
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    driver._send_w_request([0x30, variable_id], completion)
    timeout = getattr(type(driver), "REQUEST_TIMEOUT_SECONDS", 0.5)
    await asyncio.wait_for(completed.wait(), timeout)

    error = result["error"]
    if error is not None:
        raise error

    return result["value"]
