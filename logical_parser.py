import copy
import re
from collections import OrderedDict
import itertools
import pandas as pd

OPERATORS = ['&', '|', '~', '->', '!', '↑', '↓', '^']
INSTRUCTION = "Введите логическое выражение, используя следующие обозначения:\n" \
              "! - НЕ\n& - ИЛИ\n| - И\n~ - Эквивалентность\n-> - Импликация\n" \
              "↑ - Штрих Шеффера\n↓ - Стрелка Пирса\n^ - Исключающее ИЛИ(XOR)"

expression_array_old = OrderedDict()


class Element:
    """Класс элемента. Элемент может быть оператором либо выражением"""
    def __init__(self, s, mask=None):
        if s in OPERATORS:
            self.type = "operator"
        else:
            self.type = "expression"
        self.value = s
        self.mask = mask


class Expression:
    def __init__(self, expression: str):
        self.old_expression = expression
        self.VARIABLES = []
        self.results = self.table_data(self.old_expression)
        self.sknf = None
        self.sdnf = None

    def change_expression(self, new_expression: str):
        self.old_expression = new_expression
        self.VARIABLES = []
        self.results = self.table_data(self.old_expression)
        self.sknf = None
        self.sdnf = None

    def get_truth_table(self):
        return self.results

    def get_sknf(self) -> str:  # Получение СКНФ
        if self.sknf:
            return self.sknf
        self.sknf = ""
        local_sknf = []
        for values in self.results[0]:  # перебираем списки с ответами
            if values[-1] == 0:  # Берем в СКНФ, если значение = 0
                local_str = []
                for symbol, truth in zip(self.VARIABLES, values[0]):  # values[0] - значения переменных
                    local_str.append(f"{'!' if truth else ''}{symbol}")
                local_sknf.append("(" + "|".join(local_str) + ")")
        self.sknf = "&".join(local_sknf)
        if len(self.sknf) == 0:
            self.sknf = "Const 1"
        return self.sknf

    def get_sdnf(self) -> str:  # Получение СДНФ
        if self.sdnf:
            return self.sdnf
        self.sdnf = ""
        local_sdnf = []
        for values in self.results[0]:  # перебираем списки с ответами
            if values[-1] == 1:  # Берем в СКНФ, если значение = 0
                local_str = []
                for symbol, truth in zip(self.VARIABLES, values[0]):  # values[0] - значения переменных
                    local_str.append(f"{'' if truth else '!'}{symbol}")
                local_sdnf.append("(" + "&".join(local_str) + ")")
        self.sdnf = "|".join(local_sdnf)
        if len(self.sdnf) == 0:
            self.sdnf = "Const 0"
        return self.sdnf

    def get_new_mask(self, v1: str, v2: str | None, operator: str):
        """
        Строит новую запись так, чтобы минимизировать лишние скобки
        :param v1: Левая часть
        :param v2: Правая часть
        :param operator: Символ оператора
        :return:
        """
        if len(v1) == 1 and operator == "!":
            return f"!{v1}"  # отрицание единственного элемента
        if not v2 and operator == "!":
            return f"!({v1})"
        if re.fullmatch("[a-z]" + f"[{operator}][a-z]" * (len(v1) // 2), v1)\
                and re.fullmatch("[a-z]" + f"[{operator}][a-z]" * (len(v2) // 2), v2):
            return f"{v1}{operator}{v2}"  # Если все операции одинаковые, то скобки не нужны
        if len(v1) == 1:
            return f"{v1}{operator}({v2})"
        if len(v2) == 1:
            return f"({v1}){operator}{v2}"
        else:
            return f"({v1}){operator}({v2})"

    def gen_results(self, templates: dict) -> OrderedDict:
        """
        Получение промежуточных и итоговых результатов для конкретной итерации

        :param templates: Значения, подставляемые вместо переменных, в текущей итерации
        :return: Словарь [выражение:значение] в порядке получения результатов
        """
        ress = OrderedDict()
        expression_array = copy.deepcopy(expression_array_old)
        i = 0
        while len(expression_array) > 1:
            exp = expression_array[i]
            if exp.type == "operator":
                exp.type = "expression"
                match exp.value:
                    case "!":  # НЕ
                        exp.mask = self.get_new_mask(expression_array[i - 1].mask, None, "!")
                        exp.value = int(not expression_array[i - 1].value)
                        expression_array.pop(i - 1)
                    case "&":  # И
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "&")
                        exp.value = expression_array[i - 2].value and expression_array[i - 1].value
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case "|":  # ИЛИ
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "|")
                        exp.value = expression_array[i - 2].value or expression_array[i - 1].value
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case "->":  # Импликация
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "->")
                        exp.value = int(not(expression_array[i - 2].value) or expression_array[i - 1].value)
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case "~":  # Эквивалентность
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "~")
                        exp.value = int(expression_array[i - 2].value == expression_array[i - 1].value)
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case '↑':  # Штрих Шеффера
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "↑")
                        exp.value = int(not(expression_array[i - 2].value and expression_array[i - 1].value))
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case '↓':  # Стрелка Пирса
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "↓")
                        exp.value = int(not (expression_array[i - 2].value or expression_array[i - 1].value))
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                    case '^':  # XOR
                        exp.mask = self.get_new_mask(expression_array[i - 2].mask, expression_array[i - 1].mask, "^")
                        exp.value = int(expression_array[i - 2].value ^ expression_array[i - 1].value)
                        expression_array.pop(i - 1)
                        expression_array.pop(i - 2)
                        i -= 1
                ress[exp.mask] = exp.value
            else:
                if exp.mask in self.VARIABLES:
                    exp.value = templates[exp.mask]
                i += 1
        return ress

    def op_prior(self, o: str) -> int:
        """Приоритет операций
        :param o: Оператор
        :return: Уровень оператора. Чем выше, тем раньше выполняется
        """
        if o == '!':
            return 4
        elif o == '&' or o == '↑':
            return 3
        elif o == '|' or o == '^' or o == '↓':
            return 2
        elif o == '->':
            return 1
        elif o == '~':
            return 1

    def opn(self, expr: str) -> list:
        """
        Перевод выражения из инфиксной в постфиксную запись
        :param expr: Выражение в инфиксной форме
        :return: Выражение в постфиксной форме в виде поэлементного списка
        """
        co = []  # выходная строка
        op_steck = []  # стек операторов
        n = 0
        while n < len(expr) - 1:  # вставляем недостающие пробелы
            if (expr[n].isalpha() or expr[n] in ['&', '|', '~', '>', '!', '↑', '↓', '^', '(', ')']) and expr[n + 1] != " ":
                expr = expr[:n + 1] + ' ' + expr[n + 1:]
            n += 1

        list_tokens = re.split('[ ]+', expr)  # разбиваем в список по пробелам
        for i in list_tokens:  # цикл по списку- i элемент число,() или знак операции
            if i.isdigit() or i.isalpha():  # i-число или буква
                co.append(i)  # в стек
            elif i in OPERATORS:  # i - операция
                if len(op_steck) > 0:
                    token_tmp = op_steck[-1]  # смотрим на вверх стека
                    while len(op_steck) > 0 and token_tmp != '(':  # пока стек >0
                        if (self.op_prior(i) <= self.op_prior(
                                token_tmp)):  # сравнием приоритет токена в строке и приоритет операции в стеке операций
                            co.append(op_steck.pop())  # если в стеке операция выше, то выталкиваем его в выходную строку
                        else:  # иначе выходим из данного цикла
                            break
                        if len(op_steck):
                            token_tmp = op_steck[-1]
                op_steck.append(i)  # тогда выйдя из цикла, добавим операцию в стек
            elif i == '(':  # открывающая (
                op_steck.append(i)  # в стек
            elif i == ')':  # закрывающая )
                token_tmp = op_steck[-1]  # смотрим на вверх стека
                while token_tmp != '(':  # пока не встретим открывающую скобку
                    co.append(op_steck.pop())
                    # выталкиваем операторы в выходную строку, раз мы работаем с группированием чисел со скобками
                    token_tmp = op_steck[-1]  # смотрим на вверх стека внутри цикла
                    if len(op_steck) == 0:
                        raise RuntimeError('Пропущена (')
                    if token_tmp == '(':
                        op_steck.pop()

        while len(op_steck) > 0:  # мы должны вытолкнуть оставшиеся операторы
            token_tmp = op_steck[-1]
            co.append(op_steck.pop())
            if token_tmp == '(':
                raise RuntimeError('Пропущена )')
        return co

    def to_expression_array(self, simple_string: list) -> OrderedDict:
        """
        Перевод из постфиксной записи в словарь с результатами
        :param simple_string: Строка с выражением в постфиксной форме записи
        :return: Упорядоченный словарь с результатами
        """
        global expression_array_old
        for i in range(ord("a"), ord("z") + 1):
            if chr(i) in simple_string and i not in self.VARIABLES:
                self.VARIABLES.append(chr(i))

        expression_array = []
        for i in simple_string:
            if i in OPERATORS:
                expression_array.append(Element(i))
            elif i.isalpha():
                if len(i) == 1:
                    expression_array.append(Element(i, i))
                else:
                    print("Неизвестный объект!")
                    break
            else:
                print("Неизвестный объект!")
                break

        results = OrderedDict()

        expression_array_old = copy.deepcopy(expression_array)
        for i in itertools.product([0, 1], repeat=len(self.VARIABLES)):
            vars_local = dict()
            for var, value in zip(self.VARIABLES, i):
                vars_local[var] = value
            results[i] = self.gen_results(vars_local)
        return results

    def table_data(self, start_str: str) -> tuple[list, list] | tuple[bool, str]:
        """Функция для использования в Jupiter Notebook
        :param start_str: Строка с выражением в инфиксной форме
        :return: Кортеж из списка с данными и списка с названием колонок или ошибку
        """
        if not re.fullmatch("[a-z&|^~>!↑↓()\- ]{1,}", start_str):
            return False, "Некорректная запись(недопустимые символы)"

        simple_string = self.opn(start_str)
        results = self.to_expression_array(simple_string)
        table_data_array = []
        for i, values in zip(results.keys(), results.values()):
            table_data_array.append([i])
            for elem in values.values():
                table_data_array[-1].append(elem)
        table_columns_name = ""
        for i in self.VARIABLES:  # формирование названия столбца со списком переменных
            table_columns_name += f"{i} "
        table_columns_name = table_columns_name[:-1]
        first_str = list(results.keys())[0]
        table_columns = [table_columns_name]
        for i in results[first_str].keys():
            table_columns.append(i)
        pd.DataFrame(table_data_array, columns=table_columns)
        return table_data_array, table_columns


if __name__ == "__main__":
    print(INSTRUCTION)
    #simple_str = opn(input())
    # simple_str = opn("( x & y & ! w ) | ( x & y & z & ! w ) | ( x & ! y & ! z & ! w )")
    start_str = input()
    main_expression = Expression(start_str)

    results = main_expression.get_truth_table()

    print("\t".join(results[1]))  # заголовки
    for i in results[0]:
        for j in i:
            print(f"{j}\t", end="")
        print()
    print("СДНФ: ", main_expression.get_sdnf())
    print("СКНФ: ", main_expression.get_sknf())
