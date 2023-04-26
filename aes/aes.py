from aes.aes_functions import *


def encrypt(input_bytes: bytes, key: str) -> list:
    state = [[] for _ in range(4)]

    for r in range(4):
        for c in range(4):
            state[r].append(input_bytes[r + 4 * c])

    key_schedule = key_expansion(key)

    state = add_round_key(state, key_schedule)

    for rnd in range(1, nr):
        state = sub_bytes(state)
        state = shift_rows(state)
        state = mix_columns(state)
        state = add_round_key(state, key_schedule, rnd)

    state = sub_bytes(state)
    state = shift_rows(state)
    state = add_round_key(state, key_schedule, rnd + 1)

    output = [None for _ in range(4 * nb)]
    for r in range(4):
        for c in range(nb):
            output[r + 4 * c] = state[r][c]

    return output


def decrypt(cipher, key) -> list:
    state = [[] for _ in range(nb)]
    for r in range(4):
        for c in range(nb):
            state[r].append(cipher[r + 4 * c])

    key_schedule = key_expansion(key)

    state = add_round_key(state, key_schedule, nr)

    rnd = nr - 1
    while rnd >= 1:
        state = shift_rows(state, inv=True)
        state = sub_bytes(state, inv=True)
        state = add_round_key(state, key_schedule, rnd)
        state = mix_columns(state, inv=True)

        rnd -= 1

    state = shift_rows(state, inv=True)
    state = sub_bytes(state, inv=True)
    state = add_round_key(state, key_schedule, rnd)

    output = [None for _ in range(4 * nb)]
    for r in range(4):
        for c in range(nb):
            output[r + 4 * c] = state[r][c]

    return output

#
# hi = 'my name is 11112'
#
# a = hi.encode('utf-8')
# print(f'сообщение: {a}')
# cipher = encrypt(a, str(340282366920938463463374607431768211455))
# print(f'зашифрованное: {cipher}')
# message = decrypt(cipher, str(340282366920938463463374607431768211455))
# print(f'расшифрованное: {message}')
# res = ''
# for i in message:
#     print(chr(i))
