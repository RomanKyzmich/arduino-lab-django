# В файлі Core/linter.py
import re


def check_servo_values(code, max_val):
    """
Indefinido:
    Шукає 'servo.write(ЧИСЛО)' і перевіряє, чи ЧИСЛО не перевищує max_val.
    """
    # Патерн: шукає '.write(' з пробілами або без, і захоплює цифри всередині
    pattern = re.compile(r"\.write\s*\(\s*(\d+)\s*\)")

    matches = pattern.finditer(code)
    for match in matches:
        value = int(match.group(1))  # Отримуємо число (група 1)
        if value > max_val:
            # Знайдено небезпечне значення!
            return False, f"Помилка: Знайдено небезпечне значення .write({value}). Максимум для цього стенду: {max_val}."

    return True, ""  # Все чисто


def check_banned_pins(code, pins):
    """
    Шукає 'pinMode(ПІН, ...)' і перевіряє, чи ПІН не в забороненому списку.
    """
    pattern = re.compile(r"pinMode\s*\(\s*(\d+)\s*,")

    matches = pattern.finditer(code)
    for match in matches:
        pin = int(match.group(1))
        if pin in pins:
            return False, f"Помилка: Спроба використати зарезервований пін {pin}, який заборонено на цьому стенді."

    return True, ""


def validate_code(code, rules):
    """
Indefinido:
    Головна функція валідації. Приймає код і словник правил.
    """
    if 'max_servo_value' in rules:
        is_safe, msg = check_servo_values(code, rules['max_servo_value'])
        if not is_safe:
            return False, msg

    if 'banned_pins' in rules:
        is_safe, msg = check_banned_pins(code, rules['banned_pins'])
        if not is_safe:
            return False, msg

    # ...Тут ви можете додати більше правил...

    return True, "Код виглядає безпечним."