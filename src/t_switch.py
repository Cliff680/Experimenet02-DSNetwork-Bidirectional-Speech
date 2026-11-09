"""任务一：同一链路的时间交换。"""
import numpy as np
from src.models import IDLE, RESERVED, SLOTS

def t_switch(input_frame, control_memory):
    """输入uint8[32]，控制表{输出时隙:输入时隙}，返回新的uint8[32]。

    未连接输出填IDLE；TS0与TS16从输入同位置透传。
    映射的输入、输出必须是合法业务时隙，否则抛ValueError。
    不得原地修改输入帧。基础模型采用整帧缓存，时延由engine标记。
    """
    if not isinstance(input_frame, np.ndarray) or input_frame.dtype != np.uint8 or input_frame.shape != (SLOTS,):
        raise ValueError('input_frame must be a uint8 array with shape (32,)')

    output_frame = np.full(SLOTS, IDLE, dtype=np.uint8)
    for reserved_ts in RESERVED:
        output_frame[reserved_ts] = input_frame[reserved_ts]

    for output_ts, input_ts in control_memory.items():
        if (
            not isinstance(output_ts, (int, np.integer))
            or not isinstance(input_ts, (int, np.integer))
            or output_ts < 0
            or output_ts >= SLOTS
            or input_ts < 0
            or input_ts >= SLOTS
            or output_ts in RESERVED
            or input_ts in RESERVED
        ):
            raise ValueError('control mappings must use legal business timeslots')
        output_frame[output_ts] = input_frame[input_ts]

    return output_frame
