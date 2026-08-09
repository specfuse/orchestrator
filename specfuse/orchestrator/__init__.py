"""Specfuse orchestrator: initiative coordination drivers."""

from importlib import resources

__version__ = "0.5.0"


def ownership_fragment():
    """Return the filesystem path to the packaged ownership-manifest fragment."""
    return resources.files("specfuse.orchestrator").joinpath("orchestrator.ownership.yaml")
