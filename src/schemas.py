"""Definition of the models and enums used in the application."""

import enum
from typing import Any, Optional, Annotated

from pydantic import BaseModel, conlist


class Confinement(str, enum.Enum):
    """Confinement types."""
    strict = "strict"
    classic = "classic"


class Snap(BaseModel):
    """Model for a single snap."""
    name: str
    channel: str
    confinement: Confinement
    config: Optional[dict[Any, Any]] = None

class Snaps(BaseModel):
    """Model for snaps."""
    snaps: Annotated[list[Snap], conlist(Snap, min_length=0)]
