"""Experimental Nemotron 3.5 Super harness profile.

The NVIDIA API Catalog identifier is pending publication. Update these exact
model keys when the public API Catalog entry is available. This candidate has
not demonstrated an overall gain in the Super 3.5 VL Harbor comparison.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from deepagents.profiles.harness._nvidia_nemotron_3_ultra import build_nemotron_profile
from deepagents.profiles.harness.harness_profiles import HarnessProfile, _register_harness_profile_impl

if TYPE_CHECKING:
    from langchain.agents.middleware.types import AgentMiddleware

_NEMOTRON_SUPER_MODEL_SPECS: tuple[str, ...] = (
    "NVIDIA:nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16",
    "nvidia:nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16",
)


def build_nemotron_super_profile() -> HarnessProfile:
    """Adapt the Ultra profile for Super without its follow-up rewrite guard.

    The guard replaced correct final answers in the Super evaluation traces.
    Keep the other prompts and middleware while the Super profile is evaluated.
    This is a staged candidate, not a recommended release configuration.
    """
    ultra = build_nemotron_profile()

    def middleware_without_followup() -> list[AgentMiddleware]:
        return [
            middleware
            for middleware in ultra.materialize_extra_middleware()
            if middleware.name != "FollowupDisciplineMiddleware"
        ]

    return replace(ultra, extra_middleware=middleware_without_followup)


def register() -> None:
    """Register the Nemotron 3.5 Super harness profile."""
    profile = build_nemotron_super_profile()
    for spec in _NEMOTRON_SUPER_MODEL_SPECS:
        _register_harness_profile_impl(spec, profile)
