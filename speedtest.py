#!/usr/bin/env python3
"""Замер скорости скачивания: N последовательных запросов к одному URL."""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024
USER_AGENT = "speedtest-cli/1.0"


def fetch(url: str, timeout: float) -> tuple[int, float]:
    """Скачивает ответ целиком. Возвращает (байты, секунды)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    start = time.perf_counter()
    size = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)
    return size, time.perf_counter() - start


def mbit_per_s(size_bytes: int, seconds: float) -> float:
    return size_bytes * 8 / seconds / 1_000_000 if seconds > 0 else 0.0


def format_bytes(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1000 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1000
    return f"{size:.2f} GB"


def run(url: str, count: int, timeout: float) -> int:
    print(f"URL: {url}")
    print(f"Запросов: {count}\n")

    sizes: list[int] = []
    durations: list[float] = []
    for i in range(1, count + 1):
        try:
            size, seconds = fetch(url, timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            reason = getattr(error, "reason", error)
            print(f"#{i:>2}: ошибка — {reason}", file=sys.stderr)
            continue
        sizes.append(size)
        durations.append(seconds)
        print(f"#{i:>2}: {format_bytes(size):>10}  {seconds * 1000:8.1f} ms  "
              f"{mbit_per_s(size, seconds):8.2f} Mbit/s")

    if not durations:
        print("\nНи один запрос не завершился успешно.", file=sys.stderr)
        return 1

    total_bytes = sum(sizes)
    total_time = sum(durations)
    print("\nИтого")
    print(f"  Успешных запросов:     {len(durations)} из {count}")
    print(f"  Среднее время запроса: {total_time / len(durations) * 1000:.1f} ms")
    print(f"  Скачано всего:         {format_bytes(total_bytes)} ({total_bytes} B)")
    print(f"  Скорость скачивания:   {mbit_per_s(total_bytes, total_time):.2f} Mbit/s "
          f"({total_bytes / total_time / 1_000_000:.2f} MB/s)")
    return 0 if len(durations) == count else 2


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("должно быть >= 1")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Замер скорости скачивания по URL.")
    parser.add_argument("url", help="адрес, к которому стучаться (http/https)")
    parser.add_argument("-n", "--count", type=positive_int, default=10,
                        help="количество последовательных запросов (по умолчанию 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30.0,
                        help="таймаут одного запроса в секундах (по умолчанию 30)")
    args = parser.parse_args(argv)

    if not args.url.startswith(("http://", "https://")):
        parser.error("URL должен начинаться с http:// или https://")
    try:
        return run(args.url, args.count, args.timeout)
    except KeyboardInterrupt:
        print("\nПрервано.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
