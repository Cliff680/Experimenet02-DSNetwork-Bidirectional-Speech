import numpy as np
import pytest

from src.t_switch import t_switch


def test_t_switch_reorders_and_rejects_reserved_timeslots():
    input_frame = np.arange(32, dtype=np.uint8)
    original_frame = input_frame.copy()

    output_frame = t_switch(input_frame, {1: 3, 3: 1})

    assert output_frame[1] == input_frame[3]
    assert output_frame[3] == input_frame[1]
    assert output_frame[0] == input_frame[0]
    assert output_frame[16] == input_frame[16]
    assert np.array_equal(input_frame, original_frame)

    with pytest.raises(ValueError):
        t_switch(input_frame, {16: 2})