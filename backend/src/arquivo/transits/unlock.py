from collections.abc import Sequence
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def unlock_times(day: date, zone: ZoneInfo, count: int, slots: Sequence[time]) -> list[datetime]:
    if count < 0:
        raise ValueError("o número de revelações não pode ser negativo")
    if count == 0:
        return []
    if count > len(slots):
        raise ValueError("não há horários de abertura suficientes")
    if count == 1:
        selected = [slots[0]]
    elif count == len(slots):
        selected = list(slots)
    else:
        start = slots[0].hour * 60 + slots[0].minute + slots[0].second / 60
        end = slots[-1].hour * 60 + slots[-1].minute + slots[-1].second / 60
        selected = []
        for index in range(count):
            minute = round(start + (end - start) * index / (count - 1))
            hour, minute = divmod(minute, 60)
            selected.append(time(hour, minute))
    return [datetime.combine(day, slot.replace(fold=0), tzinfo=zone) for slot in selected]
