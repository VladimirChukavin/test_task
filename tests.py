import asyncio
from decimal import Decimal
from typing import Callable

from starter import recommend_price, sample_fetch_offers


def offer(
    price: Decimal, seller: str = "PARTS", delivery_days: int = 1
) -> dict[str, str | Decimal]:
    """
    Пример оффера
    :param price: Цена
    :param seller: Продавец
    :param delivery_days: Количество дней доставки
    :return: Пример оффера
    """
    return {"seller": seller, "price": Decimal(price), "delivery_days": delivery_days}


def run(
    fetch: Callable, current: str = "1000.00", minimum: str = "1.00", **kwargs
) -> dict[str, str | Decimal]:
    """
    Запуск задачи
    :param fetch: Функция, которая возвращает офферы
    :param current: Текущая цена
    :param minimum: Минимальная цена
    :param kwargs: Дополнительные параметры
    :return: Результат
    """
    return asyncio.run(
        recommend_price(fetch, Decimal(current), Decimal(minimum), **kwargs)
    )


def test_sample_from_task() -> None:
    """
    Тест на обычный расчёт.
    :return: None
    """
    res = run(sample_fetch_offers, current="4900.00", minimum="4500.00")
    assert res["price"] == Decimal("4728.00")
    assert isinstance(res["price"], Decimal)
    assert res["decision"] == "APPLY"
    assert res["reason"]


def test_source_timeout_holds() -> None:
    """
    Тест на сбой источника, превышение времени ожидания.
    :return: None
    """

    async def slow() -> dict[str, str | list[dict[str, str | Decimal | int]]]:
        """
        Имитация задержки соединения.
        :return: Пример оффера
        """
        await asyncio.sleep(10)
        return {"status": "success", "offers": [offer(Decimal("1000.00"))]}

    res = run(slow, timeout_s=0.05)
    assert (res["price"], res["decision"]) == (Decimal("1000.00"), "HOLD")
