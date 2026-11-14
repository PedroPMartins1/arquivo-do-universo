import math
from datetime import date, datetime
from zoneinfo import ZoneInfo

from arquivo.natal.chart import NatalChart
from arquivo.natal.labels import label
from arquivo.natal.settings import Body, Sign
from arquivo.transits.engine import (
    Angle,
    DailySky,
    EventKind,
    Factor,
    Revelation,
    SkyEvent,
    Transit,
)


def _degree(value: float) -> str:
    return str(math.floor(value))


def _decimal(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def _time(value: datetime, zone: str) -> str:
    return value.astimezone(ZoneInfo(zone)).strftime("%d/%m às %H:%M")


def _point_name(point: Body | Angle) -> str:
    if point is Angle.ASCENDANT:
        return "Ascendente"
    if point is Angle.MIDHEAVEN:
        return "Meio do Céu"
    return label(point)


def natal_facts(chart: NatalChart) -> str:
    lines = [
        f"{label(body.body)} em {label(body.sign)} {_degree(body.degree_in_sign)}°, "
        f"casa {body.house}" + (", retrógrado" if body.retrograde else "")
        for body in chart.bodies
    ]
    for name, longitude in (
        ("Ascendente", chart.angles.ascendant),
        ("Meio do Céu", chart.angles.midheaven),
    ):
        sign = Sign.of(longitude)
        degree = longitude % 30
        lines.append(f"{name} em {label(sign)} {_degree(degree)}°")
    lines.extend(
        f"Cúspide da casa {house.house} em {label(house.sign)} {_degree(house.degree_in_sign)}°"
        for house in chart.houses
    )
    lines.extend(
        f"{label(aspect.first)} {label(aspect.kind)} {label(aspect.second)}, "
        f"orbe {_decimal(aspect.orb)}°"
        for aspect in chart.aspects
    )
    return "\n".join(lines)


def _contacts_fact(event: SkyEvent) -> str:
    contacts = event.contacts
    if not contacts:
        return ""
    names = ", ".join(
        f"{_point_name(point)} natal" if isinstance(point, Body) else _point_name(point)
        for point in contacts
    )
    return f"; em contacto com {names}"


def _event_fact(event: SkyEvent, zone: str) -> str:
    body = label(event.body)
    at = _time(event.at, zone)
    sign = label(event.sign) if event.sign is not None else None
    house = f", na tua casa natal {event.natal_house}" if event.natal_house is not None else ""

    if event.kind is EventKind.MOON_SIGN_INGRESS:
        description = f"Lua entra em {sign}, na tua casa natal {event.natal_house}"
    elif event.kind is EventKind.SKY_ASPECT:
        assert event.aspect is not None and event.other_body is not None
        description = f"{body} em {label(event.aspect)} com {label(event.other_body)} no céu"
        return f"{description}, exato a {at}{_contacts_fact(event)}"
    elif event.kind is EventKind.SIGN_INGRESS:
        description = f"{body} entra em {sign}" if sign else f"{body} entra num signo"
    elif event.kind is EventKind.HOUSE_INGRESS:
        description = (
            f"{body} entra na tua casa natal {event.natal_house}"
            if event.natal_house is not None
            else f"{body} entra numa casa natal"
        )
    elif event.kind is EventKind.STATION_RETROGRADE:
        description = f"{body} estaciona retrógrado"
    elif event.kind is EventKind.STATION_DIRECT:
        description = f"{body} estaciona direto"
    elif event.kind is EventKind.NEW_MOON:
        description = f"Lua Nova{f' em {sign}' if sign else ''}{house}"
    elif event.kind is EventKind.FULL_MOON:
        description = f"Lua Cheia{f' em {sign}' if sign else ''}{house}"
    else:
        eclipse = "solar" if event.kind is EventKind.SOLAR_ECLIPSE else "lunar"
        kind = f" {event.eclipse_type}" if event.eclipse_type else ""
        description = f"Eclipse {eclipse}{kind}{f' em {sign}' if sign else ''}{house}"
    description += _contacts_fact(event)
    return f"{description}, a {at}"


def _transit_fact(transit: Transit, zone: str, day: date) -> str:
    body = label(transit.body)
    aspect = label(transit.kind)
    point = _point_name(transit.natal_point)
    parts = [f"{body} em trânsito em {aspect} com {point} natal (casa natal {transit.natal_house})"]
    if transit.exact:
        target = datetime.combine(day, datetime.min.time(), tzinfo=ZoneInfo(zone))
        exact = min(
            transit.exact,
            key=lambda instant: (
                abs((instant.astimezone(ZoneInfo(zone)).date() - day).days),
                abs((instant.astimezone(ZoneInfo(zone)) - target).total_seconds()),
            ),
        )
        parts.append(f"exato a {_time(exact, zone)}")
    if transit.applying is not None:
        parts.append("a aplicar" if transit.applying else "a separar")
    if transit.orb is not None:
        parts.append(f"orbe {_decimal(transit.orb)}°")
    return ", ".join((parts[0], *parts[1:]))


def _factor_fact(factor: Factor, zone: str, day: date) -> str:
    if factor.transit is not None:
        return _transit_fact(factor.transit, zone, day)
    assert factor.event is not None
    return _event_fact(factor.event, zone)


def revelation_facts(rev: Revelation, zone: str, day: date | None = None) -> str:
    local_day = day or datetime.now(ZoneInfo(zone)).date()
    if rev.transit is not None:
        fact = _transit_fact(rev.transit, zone, local_day)
    else:
        assert rev.event is not None
        fact = _event_fact(rev.event, zone)
    if rev.supporting:
        fact += "; em conjunto com: " + "; ".join(
            _factor_fact(factor, zone, local_day) for factor in rev.supporting
        )
    if rev.focus is not None:
        suffix = " natal" if isinstance(rev.focus, Body) else ""
        fact = f"Foco: {_point_name(rev.focus)}{suffix}. {fact}"
    return fact


def daily_facts(sky: DailySky, chart: NatalChart) -> tuple[str, str | None]:
    natal = natal_facts(chart)
    revelations = (
        "\n".join(
            f"{index}. {revelation_facts(revelation, sky.zone, sky.date)}"
            for index, revelation in enumerate(sky.revelations, start=1)
        )
        or "nenhum"
    )
    tomorrow = (
        revelation_facts(sky.tomorrow, sky.zone, sky.date) if sky.tomorrow is not None else None
    )
    return f"{natal}\n\n{revelations}", tomorrow
