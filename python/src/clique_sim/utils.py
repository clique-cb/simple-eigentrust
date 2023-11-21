import numpy as np
from typing import List


def split_proportionally(amount: int, limits: List[int]) -> List[int]:
    # Invariant: sum(result) == amount 
    proportions = np.array(limits) / sum(limits)
    return np.round(proportions * amount).astype(int).tolist()