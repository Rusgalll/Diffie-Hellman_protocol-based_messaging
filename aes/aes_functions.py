from configs.boxs import *


def key_expansion(key: str) -> list:
    key_symbols = [ord(symbol) for symbol in key]

    if len(key_symbols) < 4 * nk:
        for i in range(4 * nk - len(key_symbols)):
            key_symbols.append(0x01)

    key_schedule = [[] for _ in range(4)]

    for r in range(4):
        for c in range(nk):
            key_schedule[r].append(key_symbols[r + 4 * c])

    for col in range(nk, nb * (nr + 1)):
        if col % nk == 0:

            tmp = [key_schedule[row][col - 1] for row in range(1, 4)]
            tmp.append(key_schedule[0][col - 1])

            for j in range(len(tmp)):
                s_box_row = tmp[j] // 0x10
                s_box_col = tmp[j] % 0x10
                s_box_elem = s_box[16 * s_box_row + s_box_col]
                tmp[j] = s_box_elem

            for row in range(4):
                s = key_schedule[row][col - 4] ^ tmp[row] ^ rcon[row][int(col / nk - 1)]
                key_schedule[row].append(s)

        else:
            for row in range(4):
                s = key_schedule[row][col - 4] ^ key_schedule[row][col - 1]
                key_schedule[row].append(s)

    return key_schedule


def add_round_key(state: list, key_schedule: list, rnd=0) -> list:
    for col in range(nk):
        s0 = state[0][col] ^ key_schedule[0][nb * rnd + col]
        s1 = state[1][col] ^ key_schedule[1][nb * rnd + col]
        s2 = state[2][col] ^ key_schedule[2][nb * rnd + col]
        s3 = state[3][col] ^ key_schedule[3][nb * rnd + col]

        state[0][col] = s0
        state[1][col] = s1
        state[2][col] = s2
        state[3][col] = s3

    return state


def sub_bytes(state: list, inv=False) -> list:
    if not inv:
        box = s_box
    else:
        box = inv_s_box

    for i in range(len(state)):
        for j in range(len(state[i])):
            row = state[i][j] // 0x10
            col = state[i][j] % 0x10

            box_elem = box[16 * row + col]
            state[i][j] = box_elem

    return state


def shift_rows(state: list, inv=False) -> list:
    count = 1

    if not inv:
        for i in range(1, nb):
            state[i] = left_shift(state[i], count)
            count += 1
    else:
        for i in range(1, nb):
            state[i] = right_shift(state[i], count)
            count += 1

    return state


def left_shift(array: list, count: int) -> list:
    res = array[:]
    for i in range(count):
        temp = res[1:]
        temp.append(res[0])
        res[:] = temp[:]

    return res


def right_shift(array: list, count: int) -> list:
    res = array[:]
    for i in range(count):
        tmp = res[:-1]
        tmp.insert(0, res[-1])
        res[:] = tmp[:]

    return res


def mix_columns(state: list, inv=False) -> list:
    for i in range(nb):

        if not inv:
            s0 = mul_by_02(state[0][i]) ^ mul_by_03(state[1][i]) ^ state[2][i] ^ state[3][i]
            s1 = state[0][i] ^ mul_by_02(state[1][i]) ^ mul_by_03(state[2][i]) ^ state[3][i]
            s2 = state[0][i] ^ state[1][i] ^ mul_by_02(state[2][i]) ^ mul_by_03(state[3][i])
            s3 = mul_by_03(state[0][i]) ^ state[1][i] ^ state[2][i] ^ mul_by_02(state[3][i])
        else:
            s0 = mul_by_0e(state[0][i]) ^ mul_by_0b(state[1][i]) ^ mul_by_0d(state[2][i]) ^ mul_by_09(state[3][i])
            s1 = mul_by_09(state[0][i]) ^ mul_by_0e(state[1][i]) ^ mul_by_0b(state[2][i]) ^ mul_by_0d(state[3][i])
            s2 = mul_by_0d(state[0][i]) ^ mul_by_09(state[1][i]) ^ mul_by_0e(state[2][i]) ^ mul_by_0b(state[3][i])
            s3 = mul_by_0b(state[0][i]) ^ mul_by_0d(state[1][i]) ^ mul_by_09(state[2][i]) ^ mul_by_0e(state[3][i])

        state[0][i] = s0
        state[1][i] = s1
        state[2][i] = s2
        state[3][i] = s3

    return state


def mul_by_02(num):
    if num < 0x80:
        res = (num << 1)
    else:
        res = (num << 1) ^ 0x1b

    return res % 0x100


def mul_by_03(num):
    return mul_by_02(num) ^ num


def mul_by_09(num):
    # return mul_by_03(num)^mul_by_03(num)^mul_by_03(num) - works wrong, I don't know why
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ num


def mul_by_0b(num):
    # return mul_by_09(num)^mul_by_02(num)
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(num) ^ num


def mul_by_0d(num):
    # return mul_by_0b(num)^mul_by_02(num)
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(mul_by_02(num)) ^ num


def mul_by_0e(num):
    # return mul_by_0d(num)^num
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(mul_by_02(num)) ^ mul_by_02(num)
