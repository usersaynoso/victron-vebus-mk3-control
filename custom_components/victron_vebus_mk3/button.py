from __future__ import annotations

from dataclasses import dataclass
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from typing import Awaitable, Callable

from . import Context
from .capabilities import entity_supported
from .const import DOMAIN, KEY_CONTEXT
from .vebus_state import ChargeStateAction


@dataclass(kw_only=True)
class VictronMK3ButtonEntityDescription(ButtonEntityDescription):
    press_fn: Callable[[Context], Awaitable[None]]


async def force_charge_state(
    context: Context, action: ChargeStateAction, name: str
) -> None:
    await context.controller.force_charge_state(action, name)
    await context.coordinator.async_request_refresh()


ENTITY_DESCRIPTIONS: tuple[VictronMK3ButtonEntityDescription, ...] = (
    VictronMK3ButtonEntityDescription(
        key="force_equalise",
        name="Force Equalise",
        translation_key="force_equalise",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda context: force_charge_state(
            context, ChargeStateAction.FORCE_EQUALISE, "Force Equalise"
        ),
    ),
    VictronMK3ButtonEntityDescription(
        key="force_absorption",
        name="Force Absorption",
        translation_key="force_absorption",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda context: force_charge_state(
            context, ChargeStateAction.FORCE_ABSORPTION, "Force Absorption"
        ),
    ),
    VictronMK3ButtonEntityDescription(
        key="force_float",
        name="Force Float",
        translation_key="force_float",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda context: force_charge_state(
            context, ChargeStateAction.FORCE_FLOAT, "Force Float"
        ),
    ),
)


class VictronMK3ButtonEntity(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        context: Context,
        entity_description: VictronMK3ButtonEntityDescription,
    ) -> None:
        CoordinatorEntity.__init__(self, context.coordinator, entity_description.key)
        self.context = context
        self.entity_description = entity_description
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{entity_description.key}"

    async def async_press(self) -> None:
        await self.context.run_control_action(
            f"button.{self.entity_description.key}.press",
            self.entity_description.press_fn(self.context),
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    context = hass.data[DOMAIN][entry.entry_id][KEY_CONTEXT]
    async_add_entities(
        VictronMK3ButtonEntity(context, description)
        for description in ENTITY_DESCRIPTIONS
        if entity_supported(context.capabilities, description.key)
    )
