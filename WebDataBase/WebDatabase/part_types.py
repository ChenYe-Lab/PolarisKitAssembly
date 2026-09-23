"""Legacy database/API type IDs. Values must not be renumbered."""
from enum import IntEnum


class PartType(IntEnum):
    PROMOTER = 1
    CDS = 2
    TERMINATOR = 3
    RBS = 4
