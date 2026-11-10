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


def test_driver_treats_undefined_ram_variable_scale_as_unsupported() -> None:
    driver = _VictronMK3Driver()
    driver._writer = FakeWriter()
    original_queue = list(driver._variable_id_queue)
    driver._variable_info_request_time = 1

    driver._handle_variable_info_response(
        CollectingHandler(), bytes.fromhex("ff588e00808f0000")
    )

    assert driver._variable_id_queue == original_queue[1:]
    assert driver._variable_info == {original_queue[0]: None}


def test_driver_skips_unsupported_variable_short_reply() -> None:
    # Inverter-only units reply to variable 0 (AC mains voltage) with just a zero
    # scale and no offset part; discovery must move on to the next variable.
    driver = _VictronMK3Driver()
    writer = FakeWriter()
    driver._writer = writer
    driver._variable_info_request_time = 1

    driver._handle_variable_info_response(
        CollectingHandler(), bytes.fromhex("ff598e0000")
    )

    assert driver._variable_info == {0: None}
    assert driver._variable_id_queue[0] == 1
    assert writer.frames[-1][3:6] == bytes([0x36, 1, 0])


def test_driver_reports_unsupported_variables_as_none() -> None:
    driver = _VictronMK3Driver()
    driver._writer = FakeWriter()
    handler = CollectingHandler()
    while driver._variable_id_queue:
        variable_id = driver._variable_id_queue[0]
        driver._variable_info_request_time = None
        if variable_id in (0, 1, 8, 15):
            reply = "ff598e0000"
        else:
            reply = "ff598e01008f0000"  # scale 1, offset 0
        driver._handle_variable_info_response(handler, bytes.fromhex(reply))

    assert driver._ensure_variable_info_available()

    dc_frame = bytes([0x20, 0, 0, 0, 0, 0x0C, 0x18, 0x00, 5, 0, 0, 2, 0, 0, 200])
    driver._handle_frame(handler, dc_frame)
    ac_frame = bytes([0x20, 1, 1, 0, 9, 0x08, 0, 0, 0, 0, 230, 0, 7, 0, 0])
    driver._handle_frame(handler, ac_frame)
    driver._handle_power_response(
        handler, bytes([0xFF, 0x58, 0x85, 50, 0, 0, 0, 40, 0])
    )

    dc, ac, power = handler.responses
    assert dc.dc_voltage == 24
    assert dc.dc_current_to_inverter == 5
    assert dc.dc_current_from_charger == 2
    assert dc.ac_inverter_frequency == 0.05
    assert ac.ac_mains_voltage is None
    assert ac.ac_mains_current is None
    assert ac.ac_mains_frequency is None
    assert ac.ac_inverter_voltage == 230
    assert ac.ac_inverter_current == 7
    assert power.dc_power == 50
    assert power.ac_mains_power is None
    assert power.ac_inverter_power == 40


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


def _discover_variables(driver: _VictronMK3Driver, unsupported: tuple[int, ...]) -> None:
    handler = CollectingHandler()
    while driver._variable_id_queue:
        variable_id = driver._variable_id_queue[0]
        driver._variable_info_request_time = None
        reply = "ff598e0000" if variable_id in unsupported else "ff598e01008f0000"
        driver._handle_variable_info_response(handler, bytes.fromhex(reply))


class ReplyingWriter(FakeWriter):
    """Answers W-requests (X/Y/Z frames) via the driver using a reply function."""

    def __init__(self, driver: _VictronMK3Driver, handler: Handler, reply) -> None:
        super().__init__()
        self._driver = driver
        self._handler = handler
        self._reply = reply

    def write(self, msg: bytes) -> None:
        super().write(msg)
        if chr(msg[2]) in "XYZ":
            payload = self._reply(list(msg[3:-1]))
            if payload is not None:
                nonce = "XYZ".index(chr(msg[2]))
                asyncio.get_running_loop().call_soon(
                    self._driver._handle_w_response,
                    self._handler,
                    nonce,
                    bytes([0xFF, msg[2]] + payload),
                )


def _w_requests(writer: FakeWriter) -> list[list[int]]:
    return [list(frame[3:-1]) for frame in writer.frames if chr(frame[2]) in "XYZ"]


def test_power_request_uses_bundled_read_when_supported() -> None:
    async def exercise():
        driver = _VictronMK3Driver()
        handler = CollectingHandler()
        driver._writer = FakeWriter()
        _discover_variables(driver, unsupported=())
        writer = ReplyingWriter(
            driver, handler, lambda req: [0x85, 50, 0, 10, 0, 40, 0]
        )
        driver._writer = writer
        return await driver.send_power_request(), writer, handler

    power, writer, handler = asyncio.run(exercise())
    assert _w_requests(writer) == [[0x30, 14, 15, 16]]
    assert (power.dc_power, power.ac_mains_power, power.ac_inverter_power) == (
        50,
        -10,
        40,
    )
    assert handler.responses == [power]


def test_power_request_falls_back_to_single_reads_after_rejection() -> None:
    # Inverter Compact firmware 1170216 rejects the bundled read with 0x90.
    def reply(req: list[int]) -> list[int]:
        if len(req) > 2:
            return [0x90, 0x02, 0x00]
        return {14: [0x85, 50, 0], 15: [0x90, 0, 0], 16: [0x85, 40, 0]}[req[1]]

    async def exercise():
        driver = _VictronMK3Driver()
        handler = CollectingHandler()
        driver._writer = FakeWriter()
        _discover_variables(driver, unsupported=())
        writer = ReplyingWriter(driver, handler, reply)
        driver._writer = writer
        first = await driver.send_power_request()
        second = await driver.send_power_request()
        return first, second, writer

    first, second, writer = asyncio.run(exercise())
    assert _w_requests(writer) == [
        [0x30, 14, 15, 16],
        [0x30, 14],
        [0x30, 15],
        [0x30, 16],
        [0x30, 14],
        [0x30, 15],
        [0x30, 16],
    ]
    for power in (first, second):
        assert power.dc_power == 50
        assert power.ac_mains_power is None
        assert power.ac_inverter_power == 40


def test_power_request_skips_variables_discovery_marked_unsupported() -> None:
    async def exercise():
        driver = _VictronMK3Driver()
        handler = CollectingHandler()
        driver._writer = FakeWriter()
        _discover_variables(driver, unsupported=(0, 1, 15))
        writer = ReplyingWriter(driver, handler, lambda req: [0x85, req[1], 0])
        driver._writer = writer
        return await driver.send_power_request(), writer

    power, writer = asyncio.run(exercise())
    assert _w_requests(writer) == [[0x30, 14], [0x30, 16]]
    assert power.dc_power == 14
    assert power.ac_mains_power is None
    assert power.ac_inverter_power == 16


def test_power_request_skipped_when_no_power_variables_supported() -> None:
    async def exercise():
        driver = _VictronMK3Driver()
        driver._writer = FakeWriter()
        _discover_variables(driver, unsupported=(14, 15, 16))
        writer = FakeWriter()
        driver._writer = writer
        return await driver.send_power_request(), writer

    power, writer = asyncio.run(exercise())
    assert power is None
    assert writer.frames == []
