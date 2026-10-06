"""Named random-number streams derived from one master seed (§9, Randomness).

Each stream is keyed by its *name* rather than by spawn order, so adding a stream or
switching a mechanism on or off never changes the draws of any other stream. This is
what makes common-random-numbers (CRN) counterfactuals valid.
"""

from __future__ import annotations

import hashlib

import numpy as np

STREAMS: tuple[str, ...] = (
    "population",
    "network",
    "perception",
    "strategy",
    "production",
    "adaptation",
    "baselines",
    "verification",  # E0 only: random static W for analytic checks
)


def _name_key(name: str) -> int:
    """Stable 32-bit integer key for a stream name (independent of Python's hash seed)."""
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")


class RNGStreams:
    """Lazily created, name-keyed generators for one master seed.

    Parameters
    ----------
    seed
        Master seed passed to :class:`numpy.random.SeedSequence`.

    Examples
    --------
    >>> rngs = RNGStreams(42)
    >>> q = rngs["population"].lognormal(size=3)
    """

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self._cache: dict[tuple[str, ...], np.random.Generator] = {}

    def get(self, name: str, *subkeys: str | int) -> np.random.Generator:
        """Return the generator for stream ``name`` (optionally a named sub-stream of it).

        Repeated calls with the same arguments return the *same* generator object, so
        state advances as it is used. Use :meth:`fresh` for an independent restart.
        """
        key = (name, *map(str, subkeys))
        if key not in self._cache:
            self._cache[key] = self.fresh(name, *subkeys)
        return self._cache[key]

    def fresh(self, name: str, *subkeys: str | int) -> np.random.Generator:
        """Return a newly initialised generator for the stream (cache untouched)."""
        if name not in STREAMS:
            raise KeyError(f"unknown stream {name!r}; known: {STREAMS}")
        spawn_key = tuple(_name_key(str(k)) for k in (name, *subkeys))
        ss = np.random.SeedSequence(entropy=self.seed, spawn_key=spawn_key)
        return np.random.default_rng(ss)

    def __getitem__(self, name: str) -> np.random.Generator:
        return self.get(name)
