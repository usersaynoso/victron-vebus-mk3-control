from __future__ import annotations

import asyncio

from victron_vebus_mk3_protocol import (
    ConfigResponse,
    Fault,
    Handler,
    InterfaceFlags,
    ProbeResult,
    StateResponse,
    SwitchRegister,
    SwitchState,
    _ProbeHandler,
    _VictronMK3Driver,
)


class CollectingHandler(Handler):
    def __init__(self) -> None:
        self.responses = []

    def on_response(self, response) -> None:
        self.responses.append(response)


class FakeWriter:
    def __init__(self) -> None:
        self.frames: list[bytes] = []

    def write(self, msg: bytes) -> None:
        self.frames.append(bytes(msg))


def test_protocol_enums_keep_expected_wire_values() -> None:
    assert SwitchState.ON == 3
    assert SwitchState.OFF == 4
    assert InterfaceFlags.PANEL_DETECT == 0x01
    assert InterfaceFlags.STANDBY == 0x02


def test_probe_handler_maps_faults_to_probe_results() -> None:
    handler = _ProbeHandler()

    handler.on_fault(Fault.IO_ERROR)

    assert handler.result is ProbeResult.IO_ERROR


def test_driver_parses_config_response_frame() -> None:
    driver = _VictronMK3Driver()
    handler = CollectingHandler()
    switch_register = (
        SwitchRegister.DIRECT_REMOTE_SWITCH_CHARGE
        | SwitchRegister.DIRECT_REMOTE_SWITCH_INVERT
        | SwitchRegister.SWITCH_CHARGE
        | SwitchRegister.SWITCH_INVERT
    )
    frame = bytes(
        [
            0x41,
            0x00,
            0x00,
            0x00,
            0x00,
            0x91,
            0x64,
            0x00,
            0xF4,
            0x01,
            0xC8,
            0x00,
            int(switch_register),
        ]
    )

    driver._handle_frame(handler, frame)

    assert len(handler.responses) == 1
    response = handler.responses[0]
    assert isinstance(response, ConfigResponse)
    assert response.last_active_ac_input == 1
    assert response.remote_panel_detected
    assert response.num_ac_inputs == 1
    assert response.minimum_current_limit == 10.0
    assert response.maximum_current_limit == 50.0
    assert response.actual_current_limit == 20.0
    assert response.switch_register == switch_register


def test_driver_ignores_undefined_ram_variable_scale_without_crashing() -> None:
    driver = _VictronMK3Driver()
    original_queue = list(driver._variable_id_queue)
    driver._variable_info_request_time = 1

    driver._handle_variable_info_response(
        CollectingHandler(), bytes.fromhex("ff588e00808f0000")
    )

    assert driver._variable_info_request_time is None
    assert driver._variable_id_queue == original_queue
    assert driver._variable_info == {}


def test_send_state_request_writes_current_limit_frame_and_waits_for_ack() -> None:
    async def exercise() -> StateResponse | None:
        driver = _VictronMK3Driver()
        writer = FakeWriter()
        driver._writer = writer

        task = asyncio.create_task(driver.send_state_request(SwitchState.ON, 12.5))
        await asyncio.sleep(0)
        assert writer.frames == [
            bytes([7, 0xFF, ord("S"), 3, 0x7D, 0, 1, 0x80, 166])
        ]

        driver._deliver_response(CollectingHandler(), StateResponse())
        return await task

    assert isinstance(asyncio.run(exercise()), StateResponse)
