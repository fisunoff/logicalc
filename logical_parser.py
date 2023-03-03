import copy
import re
from collections import OrderedDict
import itertools
import pandas as pd

OPERATORS = ['&', '|', '~', '==', '->']
VARIABLES = []

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


def gen_results(templates: dict) -> OrderedDict:
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
                case "~":
                    exp.mask = f"~({expression_array[i - 1].mask})"
                    exp.value = int(not expression_array[i - 1].value)
                    expression_array.pop(i - 1)
                case "&":
                    exp.mask = f"({expression_array[i - 2].mask})&({expression_array[i - 1].mask})"
                    exp.value = expression_array[i - 2].value and expression_array[i - 1].value
                    expression_array.pop(i - 1)
                    expression_array.pop(i - 2)
                    i -= 1
                case "|":
                    exp.mask = f"({expression_array[i - 2].mask})|({expression_array[i - 1].mask})"
                    exp.value = expression_array[i - 2].value or expression_array[i - 1].value
                    expression_array.pop(i - 1)
                    expression_array.pop(i - 2)
                    i -= 1
                case "->":
                    exp.mask = f"({expression_array[i - 2].mask})->({expression_array[i - 1].mask})"
                    exp.value = int(not(expression_array[i - 2].value) or expression_array[i - 1].value)
                    expression_array.pop(i - 1)
                    expression_array.pop(i - 2)
                    i -= 1
                case "==":
                    exp.mask = f"({expression_array[i - 2].mask})==({expression_array[i - 1].mask})"
                    exp.value = int(expression_array[i - 2].value == expression_array[i - 1].value)
                    expression_array.pop(i - 1)
                    expression_array.pop(i - 2)
                    i -= 1
            ress[exp.mask] = exp.value
        else:
            if exp.mask in VARIABLES:
                exp.value = templates[exp.mask]
            i += 1
    return ress


def op_prior(o):
    if o == '~':
        return 4
    elif o == '&':
        return 3
    elif o == '|':
        return 2
    elif o == '->':
        return 1
    elif o == '==':
        return 1


def opn(expr: str) -> list:
    """
    Перевод выражения из инфиксной в постфиксную запись
    :param expr: Выражение в инфиксной форме
    :return: Выражение в постфиксной форме в виде поэлементного списка
    """
    co = []  # выходная строка
    op_steck = []  # стек операторов
    list_tokens = re.split('[ ]+', expr)  # разбиваем в список по пробелам
    for i in list_tokens:  # цикл по списку- i елемент число,() или знак операции
        if i.isdigit() or i.isalpha():  # i-число или буква
            co.append(i)  # в стек
        elif i in OPERATORS:  # i - операция
            token_tmp = ''  # смотрим на вверх стека
            if len(op_steck) > 0:
                token_tmp = op_steck[len(op_steck) - 1]  # смотрим на вверх стека
                while (len(op_steck) > 0 and token_tmp != '('):  # пока стек >0
                    if (op_prior(i) <= op_prior(
                            token_tmp)):  # сравнием приоритет токена в строке и приоритет операции в стеке операций
                        co.append(op_steck.pop())  # если в стеке операция выше, то выталкиваем его в выходную строку
                    else:  # иначе выходим из данного цикла
                        break
            op_steck.append(i)  # тогда выйдя из цикла, добавим операцию в стек
        elif i == '(':  # открывающая (
            op_steck.append(i)  # в стек
        elif i == ')':  # закрывающая )
            token_tmp = op_steck[len(op_steck) - 1]  # смотрим на вверх стека
            while token_tmp != '(':  # пока не встретим открывающую скобку
                co.append(
                    op_steck.pop())  # выталкиваем операторы в выходную строку-раз мы работаем с группированием чисел-со скобками
                token_tmp = op_steck[len(op_steck) - 1]  # смотрим на вверх стека внутри цикла
                if len(op_steck) == 0:
                    raise RuntimeError('V virajenii propushena (')
                if token_tmp == '(':
                    op_steck.pop()

    while (len(op_steck) > 0):  # мы должны вытолкнуть оставшиеся операторы
        token_tmp = op_steck[len(op_steck) - 1]
        co.append(op_steck.pop())
        if token_tmp == '(':
            raise RuntimeError('V virajenii propushena )')
    return co  # вернем постфиксную запись


def to_expression_array(simple_string: list):
    global VARIABLES, expression_array_old
    for i in range(ord("a"), ord("z") + 1):
        if chr(i) in simple_string:
            VARIABLES.append(chr(i))

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
    for i in itertools.product([0, 1], repeat=len(VARIABLES)):
        vars_local = dict()
        for var, value in zip(VARIABLES, i):
            vars_local[var] = value
        results[i] = gen_results(vars_local)
    return results


if __name__ == "__main__":
    simple_str = opn(input())
    print("\t", end="")
    results = to_expression_array(simple_str)
    for i in results[list(results.keys())[0]].keys():
        print(f"\t{i}", end="")
    print()

    for i, values in zip(results.keys(), results.values()):
        print(f"{i}\t", end="")
        for elem in values.values():
            print(f"{elem}\t\t", end="")
        print()

    print(simple_str)
    #print(*opn('~ a | b'))


def table_data(start_str):
    """Функция для использования в Jupiter Notebook"""
    simple_string = opn(start_str)
    results = to_expression_array(simple_string)
    table_data_array = []
    for i, values in zip(results.keys(), results.values()):
        table_data_array.append([i])
        for elem in values.values():
            table_data_array[-1].append(elem)
    table_columns_name = ""
    for i in VARIABLES:  # формирование названия столбца со списком переменных
        table_columns_name += f"{i} "
    table_columns_name = table_columns_name[:-1]
    first_str = list(results.keys())[0]
    table_columns = [table_columns_name]
    for i in results[first_str].keys():
        table_columns.append(i)
    pd.DataFrame(table_data_array, columns=table_columns)
    return table_data_array, table_columns

