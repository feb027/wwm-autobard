"""Key mapping lookup tables for Where Winds Meet instruments.

Based on the verified game key bindings:
- Natural notes: Single key press (Q-U, A-J, Z-M)
- Sharps (#): Hold SHIFT + key (only Do#, Fa#, Sol#)
- Flats (b): Hold CTRL + key (only Mib, Tib)
"""

from .enums import Pitch, NoteName


# Natural Notes (White Keys) - Single Key Press
# 3 pitches x 7 notes = 21 keys
NATURAL_KEYS: dict[Pitch, dict[NoteName, str]] = {
    Pitch.HIGH: {
        NoteName.DO: "q",
        NoteName.RE: "w",
        NoteName.MI: "e",
        NoteName.FA: "r",
        NoteName.SOL: "t",
        NoteName.LA: "y",
        NoteName.TI: "u",
    },
    Pitch.MID: {
        NoteName.DO: "a",
        NoteName.RE: "s",
        NoteName.MI: "d",
        NoteName.FA: "f",
        NoteName.SOL: "g",
        NoteName.LA: "h",
        NoteName.TI: "j",
    },
    Pitch.LOW: {
        NoteName.DO: "z",
        NoteName.RE: "x",
        NoteName.MI: "c",
        NoteName.FA: "v",
        NoteName.SOL: "b",
        NoteName.LA: "n",
        NoteName.TI: "m",
    },
}

# Sharp Notes (#) - Hold SHIFT + Key
# Only available for Do (1), Fa (4), Sol (5)
# 3 pitches x 3 notes = 9 keys
SHARP_KEYS: dict[Pitch, dict[NoteName, str]] = {
    Pitch.HIGH: {
        NoteName.DO: "q",   # Shift+Q = Do#
        NoteName.FA: "r",   # Shift+R = Fa#
        NoteName.SOL: "t",  # Shift+T = Sol#
    },
    Pitch.MID: {
        NoteName.DO: "a",   # Shift+A = Do#
        NoteName.FA: "f",   # Shift+F = Fa#
        NoteName.SOL: "g",  # Shift+G = Sol#
    },
    Pitch.LOW: {
        NoteName.DO: "z",   # Shift+Z = Do#
        NoteName.FA: "v",   # Shift+V = Fa#
        NoteName.SOL: "b",  # Shift+B = Sol#
    },
}

# Flat Notes (b) - Hold CTRL + Key
# Only available for Mi (3), Ti (7)
# 3 pitches x 2 notes = 6 keys
FLAT_KEYS: dict[Pitch, dict[NoteName, str]] = {
    Pitch.HIGH: {
        NoteName.MI: "e",   # Ctrl+E = Mib
        NoteName.TI: "u",   # Ctrl+U = Tib
    },
    Pitch.MID: {
        NoteName.MI: "d",   # Ctrl+D = Mib
        NoteName.TI: "j",   # Ctrl+J = Tib
    },
    Pitch.LOW: {
        NoteName.MI: "c",   # Ctrl+C = Mib
        NoteName.TI: "m",   # Ctrl+M = Tib
    },
}

# Notes that support sharps
SHARPS_SUPPORTED: frozenset[NoteName] = frozenset({
    NoteName.DO,
    NoteName.FA,
    NoteName.SOL,
})

# Notes that support flats
FLATS_SUPPORTED: frozenset[NoteName] = frozenset({
    NoteName.MI,
    NoteName.TI,
})
