import unittest
from assembly import AssemblyChip


def parse(program):
    # remove extra whitespaces
    return '\n'.join([line.strip() for line in program.strip().split('\n')])


class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        pass

    def tearDown(self):
        """Call after every test case."""
        pass

    def testAdd1(self):
        """Test case A. note that all test method names must begin with 'test.'"""
        chip = AssemblyChip(parse('''
        add 1
        sav
        '''))
        # run 2 instructions
        chip.run_many(2)
        assert chip.acc == 1, 'chip.acc expected 1, actual {}\n{}'.format(chip.acc, chip)
        assert chip.bak == 1, 'chip.bak expected 1, actual {}\n{}'.format(chip.bak, chip)
        assert chip.pc == 0, 'chip.pc expected 0, actual {}\n{}'.format(chip.pc, chip)

    def testAdd2(self):
        chip = AssemblyChip(parse('''
        add 1
        add 2
        sav
        '''))
        # run 2 instructions
        chip.run_many(6)
        assert chip.acc == 6, 'chip.acc expected 1, actual {}'.format(chip.acc)
        assert chip.bak == 6, 'chip.bak expected 1, actual {}'.format(chip.bak)
        assert chip.pc == 0, 'chip.pc expected 0, actual {}'.format(chip.pc)

    def testSub1(self):
        chip = AssemblyChip(parse('''
        sub 1
        sub 2
        sav
        '''))
        # run 2 instructions
        chip.run_many(6)
        assert chip.acc == -6, 'chip.acc expected 1, actual {}'.format(chip.acc)
        assert chip.bak == -6, 'chip.bak expected 1, actual {}'.format(chip.bak)
        print(chip)

    def testSwp(self):
        chip = AssemblyChip(parse('''
        add 1
        sav
        add 3
        swp
        '''))
        chip.run()
        chip.run()
        assert chip.acc == 1
        assert chip.bak == 1
        assert chip.pc == 2
        chip.run()
        assert chip.acc == 4
        assert chip.bak == 1
        assert chip.pc == 3
        chip.run()
        assert chip.acc == 1
        assert chip.bak == 4
        assert chip.pc == 0

    def testNeg(self):
        chip = AssemblyChip(parse('''
        add 12
        sav
        neg
        '''))
        chip.run_many(3)
        assert chip.acc == -12
        assert chip.bak == 12
        assert chip.pc == 0

    def testMovAcc(self):
        chip = AssemblyChip(parse('''
        mov 12, acc
        nop
        '''))
        chip.run()
        assert chip.acc == 12, '\n'+str(chip)
        assert chip.bak == 0
        assert chip.pc == 1

if __name__ == '__main__':
    # run all tests
    unittest.main()

