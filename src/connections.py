"""任务三与四：双向连接控制与释放。"""
from src.models import validate_endpoint, directions

def connect_pair(connection_id, endpoint_a, endpoint_b, tables):
    """原地建立双向T→S映射，成功返回True。

    非法端口或两端相同抛ValueError。ID已存在、端口已占用、
    内部T输出或S输出资源冲突，返回False且tables完全不变。
    方向src→dst：T[src.link_id][dst.timeslot]=src.timeslot；
    S[(dst.link_id,dst.timeslot)]=src.link_id。
    两个方向全部检查通过才写表，并记录pairs[id]=(a,b)。
    本实验固定路径可能发生内部阻塞，不要求自动改走其他路径。
    """
    validate_endpoint(endpoint_a)
    validate_endpoint(endpoint_b)
    if endpoint_a == endpoint_b:
        raise ValueError('连接两端必须是不同端点')
    if connection_id in tables.pairs:
        return False
    if any(endpoint_a in pair or endpoint_b in pair for pair in tables.pairs.values()):
        return False

    pending_t = []
    pending_s = []
    pending_directions = directions(endpoint_a, endpoint_b)
    for source, destination in pending_directions:
        t_key = destination.timeslot
        s_key = (destination.link_id, destination.timeslot)
        if t_key in tables.t_maps[source.link_id] or s_key in tables.s_map:
            return False
        pending_t.append((source.link_id, t_key, source.timeslot))
        pending_s.append((s_key, source.link_id))

    for link_id, output_ts, input_ts in pending_t:
        tables.t_maps[link_id][output_ts] = input_ts
    for output, input_link in pending_s:
        tables.s_map[output] = input_link
    tables.pairs[connection_id] = (endpoint_a, endpoint_b)
    return True

def disconnect_pair(connection_id, tables):
    """释放指定ID的两个方向及pairs记录，成功返回True。

    不存在或重复释放返回False，不能影响其他连接。
    输出回到IDLE由未连接映射的T/S发送规则自然产生。
    """
    pair = tables.pairs.get(connection_id)
    if pair is None:
        return False

    pending_t = []
    pending_s = []
    for source, destination in directions(*pair):
        t_key = destination.timeslot
        s_key = (destination.link_id, destination.timeslot)
        if t_key not in tables.t_maps[source.link_id] or s_key not in tables.s_map:
            return False
        pending_t.append((source.link_id, t_key))
        pending_s.append(s_key)

    for link_id, output_ts in pending_t:
        del tables.t_maps[link_id][output_ts]
    for output in pending_s:
        del tables.s_map[output]
    del tables.pairs[connection_id]
    return True
