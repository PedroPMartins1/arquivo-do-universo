from datetime import date, datetime
from zoneinfo import ZoneInfo

from arquivo.natal.chart import NatalChart
from arquivo.natal.labels import label
from arquivo.natal.settings import Body, Sign
from arquivo.transits.engine import Angle, DailySky, EventKind, Revelation


def _degree(value: float) -> str:
    return str(round(value))


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
    lines.extend(f"Cúspide da casa {house.house} em {label(house.sign)}" for house in chart.houses)
    lines.extend(
        f"{label(aspect.first)} {label(aspect.kind)} {label(aspect.second)}, "
        f"orbe {_decimal(aspect.orb)}°"
        for aspect in chart.aspects
    )
    return "\n".join(lines)


def _event_fact(revelation: Revelation, zone: str) -> str:
    event = revelation.event
    if event is None:
        return ""
    body = label(event.body)
    at = _time(event.at, zone)
    sign = label(event.sign) if event.sign is not None else None
    house = f", na tua casa natal {event.natal_house}" if event.natal_house is not None else ""

    if event.kind is EventKind.SIGN_INGRESS:
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
        if event.contacts:
            contacts = ", ".join(
                f"{_point_name(point)} natal" if isinstance(point, Body) else _point_name(point)
                for point in event.contacts
            )
            description += f"; em contacto com {contacts}"
    return f"{description}, a {at}"


def _transit_fact(revelation: Revelation, zone: str, day: date) -> str:
    transit = revelation.transit
    if transit is None:
        return ""
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


def revelation_facts(rev: Revelation, zone: str, day: date | None = None) -> str:
    if rev.transit is not None:
        return _transit_fact(rev, zone, day or datetime.now(ZoneInfo(zone)).date())
    return _event_fact(rev, zone)


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
