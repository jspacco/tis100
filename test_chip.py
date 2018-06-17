import unittest
from assembly import AssemblyChip, READ, WRITE, RUN, global_inc

'''
TODO:
* jmp to label with label on the same line
* jez
* jnz
* jgz
* jlz
* bounds checks for add/subtract/move with acc
* move constant values to a port / receive constants from port to acc
'''

DEBUG = True


def debug(msg):
    if DEBUG:
        print(str(msg))


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
        self.assertTrue(chip.acc == 1, 'chip.acc expected 1, actual {}\n{}'.format(chip.acc, chip))
        self.assertTrue(chip.bak == 1, 'chip.bak expected 1, actual {}\n{}'.format(chip.bak, chip))
        self.assertTrue(chip.pc == 0, 'chip.pc expected 0, actual {}\n{}'.format(chip.pc, chip))

    def testAdd2(self):
        chip = AssemblyChip(parse('''
        add 1
        add 2
        sav
        '''))
        # run 2 instructions
        chip.run_many(6)
        self.assertTrue(chip.acc == 6)
        self.assertTrue(chip.bak == 6)
        self.assertTrue(chip.pc == 0)

    def testSub1(self):
        chip = AssemblyChip(parse('''
        sub 1
        sub 2
        sav
        '''))
        # run 2 instructions
        chip.run_many(6)
        self.assertTrue(chip.acc == -6, 'chip.acc expected 1, actual {}'.format(chip.acc))
        self.assertTrue(chip.bak == -6, 'chip.bak expected 1, actual {}'.format(chip.bak))
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
        self.assertTrue(chip.acc == 1)
        self.assertTrue(chip.bak == 1)
        self.assertTrue(chip.pc == 2)
        chip.run()
        self.assertTrue(chip.acc == 4)
        self.assertTrue(chip.bak == 1)
        self.assertTrue(chip.pc == 3)
        chip.run()
        self.assertTrue(chip.acc == 1)
        self.assertTrue(chip.bak == 4)
        self.assertTrue(chip.pc == 0)

    def testNeg(self):
        chip = AssemblyChip(parse('''
        add 12
        sav
        neg
        '''))
        chip.run_many(3)
        self.assertTrue(chip.acc == -12)
        self.assertTrue(chip.bak == 12)
        self.assertTrue(chip.pc == 0)

    def testMovAcc(self):
        chip = AssemblyChip(parse('''
        mov 12, acc
        nop
        '''))
        chip.run()
        self.assertTrue(chip.acc == 12)
        self.assertTrue(chip.bak == 0)
        self.assertTrue(chip.pc == 1)

    def testWrapAround3(self):
        chip = AssemblyChip(parse('''
        add 10
        add 10
        add 10
        '''))
        chip.run_many(3)
        self.assertTrue(chip.acc == 30)
        self.assertTrue(chip.bak == 0)
        self.assertTrue(chip.pc == 0)

    def testWriteNumReadNumAcc(self):
        chip1 = AssemblyChip(parse('''
        mov 12, right
        nop
        '''))
        chip2 = AssemblyChip(parse('''
        mov left, acc
        nop
        '''))
        chip1.right = chip2
        chip2.left = chip1

        debug('\n' + str(chip1))
        debug('\n' + str(chip2))

        chip1.run()
        chip2.run()

        self.assertTrue(chip1.state == WRITE, '\n'+str(chip1))
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip2.state == READ, '\n'+str(chip2))
        self.assertTrue(chip2.pc == 0)

        global_inc()

        debug('\n' + str(chip1))
        debug('\n' + str(chip2))

        chip1.run()
        chip2.run()

        debug('\n' + str(chip1))
        debug('\n' + str(chip2))

        debug('chip1.pc = {}'.format(chip1.pc))
        debug('chip2.pc = {}'.format(chip2.pc))

        self.assertTrue(chip1.state == RUN, '\n' + str(chip1))
        self.assertTrue(chip1.pc == 1)
        self.assertTrue(chip2.state == RUN, '\n' + str(chip2))
        self.assertTrue(chip2.pc == 1)
        self.assertTrue(chip2.acc == 12)

    def testReadWriteTwice(self):
        # Make sure we can bounce a value back and forth
        chip1 = AssemblyChip(parse('''
        mov 12, right
        add right
        '''))
        chip2 = AssemblyChip(parse('''
        mov left, acc
        mov acc, left
        '''))
        chip1.right = chip2
        chip2.left = chip1

        debug('before cycle 1')
        debug(str(chip1))
        debug(str(chip2))

        chip1.run()
        chip2.run()
        global_inc()

        # both should be in read/write state after 1 cycle
        self.assertTrue(chip1.state == WRITE, str(chip1))
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip2.state == READ, str(chip2))
        self.assertTrue(chip2.pc == 0)

        debug('CYCLE: after 1, before 2')
        debug(str(chip1))
        debug(str(chip2))

        chip1.run()
        chip2.run()
        global_inc()

        # after 2 cycles, chip1/chip2 should complete their reads and writes
        debug('CYCLE: after 2, before 3')
        debug(str(chip1))
        debug(str(chip2))

        self.assertTrue(chip1.state == RUN)
        self.assertTrue(chip1.pc == 1)
        self.assertTrue(chip2.state == RUN)
        self.assertTrue(chip2.pc == 1)
        self.assertTrue(chip2.acc == 12)

        chip1.run()
        chip2.run()
        global_inc()

        debug('CYCLE: after 3, before 4')
        debug(str(chip1))
        debug(str(chip2))

        # back into read/write states
        self.assertTrue(chip1.state == READ)
        self.assertTrue(chip2.state == WRITE)
        self.assertTrue(chip1.pc == 1)
        self.assertTrue(chip2.pc == 1)

        chip1.run()
        chip2.run()
        global_inc()

        # now receive a read and finish a write
        debug('CYCLE: after 4, before 5')
        debug(str(chip1))
        debug(str(chip1))

        self.assertTrue(chip1.state == RUN)
        self.assertTrue(chip2.state == RUN)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip2.pc == 0)

    def testJmp(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
        jmp label
        add 10
        label:
        add 5
        '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 5)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 2)

    def testJmpLabelSameLine(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
        jmp label
        add 10
        label: add 5
        '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 5)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 2)

    def testJmpLabelSameLineSpaces(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
        jmp label
        add 10
        label: add 5
        
        
        '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 5)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 2)

    def testJez(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            jez label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 5)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 2)

    def testJez2(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            add 10
            jez label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertEquals(110, chip1.acc)
        self.assertTrue(chip1.pc == 3)
        self.assertTrue(chip1.cycle == 3)

    def testJnz(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            add 10
            jnz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 15)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJnz2(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            jnz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 105)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJgz(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            add 10
            jgz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 15)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJgz2(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            jgz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 105)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJlz(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            sub 10
            jlz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == -5)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJlz2(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            jlz label
            add 100
            label: add 5
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertTrue(chip1.acc == 105)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)

    def testJro(self):
        # test jumping to a label
        chip1 = AssemblyChip(parse('''
            add 3
            jro acc
            add 100
            add 200
            add 300
            '''))

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        chip1.run()
        debug(chip1)

        self.assertEquals(303, chip1.acc)
        self.assertTrue(chip1.pc == 0)
        self.assertTrue(chip1.cycle == 3)


def run_all():
    unittest.main()


def run_some():
    t = SimpleTestCase()
    '''
    t.testReadWriteTwice()
    t.testWrapAround3()
    t.testJmp()
    t.testJmpLabelSameLine()
    t.testJmpLabelSameLineSpaces()
    t.testJez()
    t.testJez2()
    t.testJnz()
    t.testJnz2()
    t.testJgz()
    t.testJgz2()
    t.testJlz()
    t.testJlz2()
    '''
    t.testJro()


if __name__ == '__main__':
    # run all tests
    run_some()

