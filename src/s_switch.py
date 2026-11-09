"""任务二：同一时隙位置的空间交换。"""
import numpy as np
from src.models import IDLE, RESERVED, SLOTS, LINKS

def s_switch(input_frames, spatial_map):
    """输入uint8[2,32]，控制表{(输出链路,时隙):输入链路}。

    返回新的uint8[2,32]，S只改链路，不改时隙。
    未连接业务输出填IDLE；各输出链路TS0/16保留本链路输入。
    非法链路、时隙或保留时隙映射抛ValueError，不改输入。
    """
    if (
        not isinstance(input_frames, np.ndarray)
        or input_frames.dtype != np.uint8
        or input_frames.shape != (LINKS, SLOTS)
    ):
        raise ValueError('input_frames must be a uint8 array with shape (2, 32)')

    output_frames = np.full((LINKS, SLOTS), IDLE, dtype=np.uint8)
    for reserved_ts in RESERVED:
        output_frames[:, reserved_ts] = input_frames[:, reserved_ts]

    for output, input_link in spatial_map.items():
        if (
            not isinstance(output, tuple)
            or len(output) != 2
            or not isinstance(output[0], (int, np.integer))
            or not isinstance(output[1], (int, np.integer))
            or not isinstance(input_link, (int, np.integer))
        ):
            raise ValueError('spatial mappings must use (output_link, timeslot): input_link')

        output_link, timeslot = output
        if (
            output_link < 0
            or output_link >= LINKS
            or input_link < 0
            or input_link >= LINKS
            or timeslot < 0
            or timeslot >= SLOTS
            or timeslot in RESERVED
        ):
            raise ValueError('spatial mappings must use valid links and business timeslots')
        output_frames[output_link, timeslot] = input_frames[input_link, timeslot]

    return output_frames
