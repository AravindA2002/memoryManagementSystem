from __future__ import annotations
import numpy as np
from typing import Iterable

def to_np(a: Iterable[float]) -> np.ndarray:
    return np.asarray(list(a), dtype=np.float32)

def cosine_sim(x: np.ndarray, y: np.ndarray) -> float:
    # both should be normalized already but stay safe
    nx = x / (np.linalg.norm(x) + 1e-12)
    ny = y / (np.linalg.norm(y) + 1e-12)
    return float(np.dot(nx, ny))
