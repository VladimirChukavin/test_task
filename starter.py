"""Учебный фрагмент для тестового задания ТОЛЬКООПТ.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
В функции recommend_price намеренно есть ошибки. Исправьте её по правилам ниже.
sample_fetch_offers имитирует внешний источник: реальные запросы не нужны.

Контракт fetch_offers(): async-функция без аргументов, возвращает словарь
со status (success / partial / error) и offers (список предложений).
Все суммы на входе — положительные Decimal с точностью до копейки.
seller — строка; delivery_days — неотрицательное целое число или None.
Формат входных данных корректен; дополнительных проверок типов не требуется.
fetch_offers может завершиться исключением или долго ожидать ответа.
current_price — текущая цена; min_price — минимально допустимая цена.
timeout_s — положительное число секунд, по умолчанию 2.

ПРАВИЛА В ПОРЯДКЕ ПРИМЕНЕНИЯ
1. Ограничьте ожидание fetch_offers значением timeout_s. При ошибке источника,
   тайм-ауте или status != success верните текущую цену и HOLD.
2. Учитывайте предложения с известной доставкой не более 6 дней.
   Исключайте собственный магазин MYSHOP независимо от регистра букв.
3. Если подходящих предложений нет, верните текущую цену и HOLD,
   даже если текущая цена ниже min_price.
4. Минимальную цену подходящего конкурента уменьшите на 1,5% и округлите
   вниз до копейки. Рекомендация — максимум из этой суммы и min_price.
5. Если рекомендация отличается от текущей цены более чем на 30% в любую
   сторону, верните рекомендацию и REVIEW. Иначе — рекомендацию и APPLY.
   Ровно 30% допускается. REVIEW означает, что автоматическое применение
   запрещено до ручной проверки.

РЕЗУЛЬТАТ
Словарь с полями price (Decimal), decision (APPLY / REVIEW / HOLD),
reason (короткая понятная причина). Сохраните интерфейс recommend_price;
вспомогательные функции допустимы. Пример ниже после исправления должен
вернуть price = Decimal("4728.00"), decision = "APPLY".

ПРОВЕРКА
Добавьте минимум два автоматических теста: обычный расчёт и один сбой
или граничный случай на ваш выбор. Укажите команду запуска тестов.
Достаточно стандартной библиотеки; pytest также допустим.
"""

import asyncio
from decimal import ROUND_DOWN, Decimal
from typing import Callable

OWN_SHOP = "myshop"
MAX_DELIVERY_DAYS = 6
DISCOUNT_FACTOR = Decimal("0.985")
MAX_CHANGE_RATIO = Decimal("0.30")
ROUNDING_VALUE = Decimal("0.01")
CURRENT_PRICE = Decimal("4900.00")
MIN_PRICE = Decimal("4500.00")


def _result(price: Decimal, decision: str, reason: str) -> dict[str, str | Decimal]:
    """
    Возвращает данные в оформленном виде.
    :param price: Цена
    :param decision: Решение
    :param reason: Причина
    :return: Результат в оформленном виде
    """
    return {"price": price, "decision": decision, "reason": reason}


def _is_suitable(offer: dict[str, str | Decimal | int]) -> bool:
    """
    Проверяет выполнение условий: известная доставка
    не более 6 дней и не собственный магазин.
    :param offer: Данные для проверки
    :return: True | False
    """
    delivery_days = offer["delivery_days"]
    return (
        delivery_days is not None
        and delivery_days <= MAX_DELIVERY_DAYS
        and offer["seller"].casefold() != OWN_SHOP
    )


async def recommend_price(
    fetch_offers: Callable,
    current_price: Decimal,
    min_price: Decimal,
    timeout_s: float = 2.0,
) -> dict[str, str | Decimal]:
    """
    Выбирает наиболее подходящую цену из предложенных.
    :param fetch_offers: Список предложений с ценами
    :param current_price: Текущая цена
    :param min_price: Минимальная подходящая цена
    :param timeout_s: Время ожидания ответа источника
    :return: Выбранная подходящая цена
    """
    # 1. Ограниченное ожидание источника; любой сбой; status != success -> current_price и HOLD.
    try:
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)
    except (asyncio.TimeoutError, TimeoutError):
        return _result(current_price, "HOLD", f"Источник не ответил за {timeout_s} с")
    except Exception as exc:  # noqa: BLE001
        return _result(current_price, "HOLD", f"Ошибка источника: {type(exc).__name__}")

    status = result.get("status")
    if status != "success":
        return _result(
            current_price, "HOLD", f"Неполные данные источника: status={status}"
        )

    # 2. Отбор подходящих предложений.
    prices = [
        offer["price"] for offer in result.get("offers", []) if _is_suitable(offer)
    ]

    # 3. Нет подходящих предложений -> HOLD (даже если current_price < min_price).
    if not prices:
        return _result(current_price, "HOLD", "Нет подходящих предложений конкурентов")

    # 4. Минимальная цена конкурента минус 1,5%, округление вниз до копейки, цена не ниже min_price.
    competitor_price = min(prices)
    discounted = (competitor_price * DISCOUNT_FACTOR).quantize(
        ROUNDING_VALUE, rounding=ROUND_DOWN
    )
    recommended = max(discounted, min_price)
    floor_note = " (ограничено min_price)" if recommended > discounted else ""

    # 5. Отклонение от текущей цены больше 30% -> REVIEW; ровно 30% допустимо.
    if abs(recommended - current_price) > current_price * MAX_CHANGE_RATIO:
        return _result(
            recommended,
            "REVIEW",
            f"Отклонение от текущей цены более 30%{floor_note}, нужна ручная проверка",
        )
    return _result(
        recommended,
        "APPLY",
        f"Минимальная цена конкурента {competitor_price} минус 1,5%{floor_note}",
    )


async def sample_fetch_offers() -> (
    dict[str, str | list[dict[str, str | Decimal | int]]]
):
    """
    Загружает список предложений с ценами.
    :return: Список предложений
    """
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


if __name__ == "__main__":
    print(
        asyncio.run(
            recommend_price(
                sample_fetch_offers,
                current_price=CURRENT_PRICE,
                min_price=MIN_PRICE,
            )
        )
    )
