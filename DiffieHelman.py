import random
from math import sqrt


class DiffieHelm:
    def __init__(self):
        self.a = None
        self.g = None
        self.p = None
        self.residue_division = None
        self.__key = None

    def _generate_a(self, number: int) -> None:
        self.a = random.getrandbits(number)

    @staticmethod
    def get_low_level_prime(n: int) -> int:
        first_primes_list = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
                             31, 37, 41, 43, 47, 53, 59, 61, 67,
                             71, 73, 79, 83, 89, 97, 101, 103,
                             107, 109, 113, 127, 131, 137, 139,
                             149, 151, 157, 163, 167, 173, 179,
                             181, 191, 193, 197, 199, 211, 223,
                             227, 229, 233, 239, 241, 251, 257,
                             263, 269, 271, 277, 281, 283, 293,
                             307, 311, 313, 317, 331, 337, 347, 349]
        while True:
            pc = random.getrandbits(n)
            for divisor in first_primes_list:
                if pc % divisor == 0 and divisor ** 2 <= pc:
                    break
            else:
                return pc

    @staticmethod
    def is_miller_rabin_passed(mrc) -> bool:
        max_divisions_by_two = 0
        ec = mrc - 1
        while ec % 2 == 0:
            ec >>= 1
            max_divisions_by_two += 1
        assert (2 ** max_divisions_by_two * ec == mrc - 1)

        def trial_composite(round_test: int) -> bool:
            if pow(round_test, ec, mrc) == 1:
                return False
            for k in range(max_divisions_by_two):
                if pow(round_test, 2 ** k * ec, mrc) == mrc - 1:
                    return False
            return True

        number_of_rabin_trials = 20
        for i in range(number_of_rabin_trials):
            round_tester = random.randrange(2, mrc)
            if trial_composite(round_tester):
                return False
        return True

    def _generate_p(self, number: int) -> None:
        while True:
            prime_candidate = self.get_low_level_prime(number)
            if not self.is_miller_rabin_passed(prime_candidate):
                continue
            else:
                self.p = prime_candidate
                break

    @staticmethod
    def find_prime_factors(s: set, n: int) -> None:
        while n % 2 == 0:
            s.add(2)
            n = n // 2

        for i in range(3, int(sqrt(n)), 2):
            while n % i == 0:
                s.add(i)
                n = n // i
        if n > 2:
            s.add(n)

    def find_primitive(self, n: int) -> int:
        s = set()

        if not self.is_miller_rabin_passed(n):
            return -1

        phi = n - 1
        self.find_prime_factors(s, phi)

        for r in range(2, phi + 1):
            flag = False
            for it in s:
                if pow(r, phi // it, n) == 1:
                    flag = True
                    break
            if not flag:
                return r
        return -1

    def _generate_g(self) -> None:
        self.g = self.find_primitive(self.p)

    def _generate_residue_division(self):
        self.residue_division = pow(self.g, self.a, self.p)

    def generate_parameters(self) -> None:
        self._generate_a(50)
        print(self.a)
        self._generate_p(50)
        print(self.p)
        self._generate_g()
        print(self.g)
        self._generate_residue_division()
        print(self.residue_division)
