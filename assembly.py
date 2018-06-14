import re
from logger import *


# globals
# states
RUN = 'run'
READ = 'read'
WRITE = 'wrte'
PASS = 'pass'

# directions / destinations
UP = 'up'
RIGHT = 'right'
DOWN = 'down'
LEFT = 'left'
ANY = 'any'
LAST = 'last'
NIL = 'nil'

# opcodes
NOP = 'nop'
MOV = 'mov'
ADD = 'add'
SUB = 'sub'
NEG = 'neg'
SWP = 'swp'
SAV = 'sav'
JMP = 'jmp'
JEZ = 'jez'
JNZ = 'jnz'
JLZ = 'jlz'
JGZ = 'jgz'
JRO = 'jro'

# other constants
ACC = 'acc'
ACC_ADD = 'acc_add'
ACC_SUB = 'acc_sub'
ACC_MOV = 'acc_mov'


def reverse(direction):
    if direction == UP:
        return DOWN
    if direction == DOWN:
        return UP
    if direction == RIGHT:
        return LEFT
    if direction == LEFT:
        return RIGHT
    raise Exception('unknown direction: {}'.format(direction))


def is_number(text):
    return re.match('-?\d+', text) is not None


def global_inc():
    AssemblyChip.global_pc += 1


class AssemblyChip:
    # ops = 'add sub neg mov swp sav jro jmp jez jnz jgz jlz'.split()
    global_pc = 0
    chip_num = 1

    def __init__(self, program=None, name=None):
        # TODO track the number of instructions executed in order to track idle percentage
        # name of this chip
        if name is None:
            self.name = 'chip{}'.format(AssemblyChip.chip_num)
        else:
            self.name = name
        AssemblyChip.chip_num += 1
        # current program counter, relative to list of instructions
        self.pc = 0
        # current state of this chip, which can be RUN, READ, WRITE
        self.state = RUN
        # buffer for storing values to read/write
        self.buffer = None
        # register values
        self.acc = 0
        self.bak = 0
        # list of instructions (limited to 15)
        self.instructions = []
        self.labels = {}
        # neighboring chips
        self.up = None
        self.right = None
        self.down = None
        self.left = None
        if program:
            self.parse(program)

    def parse(self, program):
        # TODO enforce 15 as max number of instructions
        program = program.lower()
        self.instructions = []
        for line in program.splitlines():
            # TODO limit instructions to 20 chars in length
            # remove comments
            # TODO: keep comments, but skip in pcinc() method
            i = line.find('#')
            if i >= 0:
                line = line[:i]
            # find labels
            if ':' in line:
                label, line = line.split(':')
                label = label.strip()
                self.labels[label] = len(self.instructions)
            line = line.strip()
            self.instructions.append(line)

    def check_label(self, label):
        if label not in self.labels:
            raise Exception('unknown label {} at line {}'.format(label, self.pc))

    def get_neighbor(self, direction):
        if direction == UP:
            return self.up
        if direction == RIGHT:
            return self.right
        if direction == DOWN:
            return self.down
        if direction == LEFT:
            return self.left
        raise Exception('unknown direction {}'.format(direction))

    def write_state(self, direction, value):
        # change our state
        self.state = WRITE
        self.buffer = (AssemblyChip.global_pc, direction, value)

    def read_state(self, direction, destination):
        # go into a read state
        self.state = READ
        self.buffer = (AssemblyChip.global_pc, direction, destination)

    def run_state(self):
        # go into run state, clear the read/write buffer
        self.state = RUN
        self.buffer = None

    def try_read(self):
        assert(self.state == READ)
        # try to fulfill a read request
        # will either be successful, or not
        (cycle, direction, destination) = self.buffer
        # TODO if direction is "any" loop through
        other = self.get_neighbor(direction)

        debug('{} read from {}'.format(self.name, direction))
        debug('{} other.buffer name = {}, state = {}, buffer = {}'.format(self.name, other.name, other.state, other.buffer))

        # check that the other chip did a write
        if other.state == WRITE:

            debug('{} reading from {}'.format(self.name, other.name))

            (other_cycle, other_direction, value) = other.buffer
            # can fulfill if other chip write in our direction at least one cycle ago
            # of if both the read and the write are the same cycle, but it is an earlier cycle
            # TODO will any nonzero difference in the read/write cycles actually work?
            if direction == reverse(other_direction) and \
                    (cycle < other_cycle or cycle == other_cycle and cycle < AssemblyChip.global_pc):

                # CASCADE
                # if the destination of our read is a port leading to another chip
                # then we write the value this cycle
                # TODO handle ANY/LAST
                if destination in [LEFT, UP, RIGHT, DOWN, ANY, LAST]:
                    self.write_state(destination, value)
                    # read value from one port, but now writing to another port
                    # so the read has not succeeded
                    return False

                # if destination is nil or a register, we go back into a run state next cycle
                if destination == ACC_ADD:
                    self.add(value)
                elif destination == ACC_SUB:
                    self.sub(value)
                elif destination == ACC_MOV:
                    self.set_acc(value)
                elif destination == NIL:
                    pass
                # We fulfilled the read we were working on, yay!
                return True
        return False

    def try_write(self):
        assert(self.state == WRITE)
        (cycle, direction, value) = self.buffer
        other = self.get_neighbor(direction)

        debug('{} try_write cycle={} direction={} value={}'.format(self.name, cycle, direction, value))
        debug('{} other.buffer {} = {}'.format(self.name, other.state, other.buffer))

        if other.state == READ:
            # try to fulfill the read from the other side
            # this is because reads can cascade, while writes cannot
            # i.e. the destination of a read could be acc, or a port
            # while a write just needs a read on the other side to work
            return other.try_read()
        # not able to fulfill a write yet
        return False

    def run_many(self, num):
        for i in range(num):
            self.run()

    def run(self):
        if self.state == PASS:
            pass
        elif self.state == READ:
            # try to fulfill the read
            debug('{} trying to fulfill a read'.format(self.name))
            result = self.try_read()
            if result:
                # TODO should pcinc() be part of run_state() method?
                debug('{} fulfilled read'.format(self.name))
                self.run_state()
                self.pcinc()
            else:
                debug('{} unable to fulfill read'.format(self.name))
        elif self.state == WRITE:
            # try to fulfill a write
            debug('{} trying to fulfill a write'.format(self.name))
            result = self.try_write()
            if result:
                # TODO should pcinc() be part of run_state() method?
                debug('{} fulfilled write'.format(self.name))
                self.run_state()
                self.pcinc()
            else:
                debug('{} unable to fulfill write'.format(self.name))

        elif self.state == RUN:
            if not self.instructions:
                return
            instruction = self.instructions[self.pc].replace(',', '')
            parts = instruction.split()
            opcode = parts.pop(0)
            trace('opcode is {}'.format(opcode))
            # TODO: assert rest of line is empty after we've processed an instruction
            # maybe split into jumps and not jumps?
            if opcode == NOP or (opcode == ADD and parts[0] == NIL):
                # simplest two kinds of nop
                pass
            elif opcode == MOV:
                src = parts.pop(0)
                dst = parts.pop(0)

                if is_number(src) and dst == NIL:
                    # basically a nop
                    # MOV 17, NIL
                    pass
                elif is_number(src) and dst == ACC:
                    # move constant into acc
                    # MOV 55, ACC
                    self.set_acc(int(src))
                elif is_number(src) and dst in [LEFT, UP, RIGHT, DOWN, ANY, LAST]:
                    # WRITE: move a constant to a port
                    # MOV 17, LEFT
                    # MOV 5, ANY
                    self.write_state(dst, int(src))
                elif src == ACC:
                    # WRITE: move acc to a port
                    # MOV ACC, LEFT
                    # MOV ACC, ACC
                    # TODO: moving to NIL is a nop
                    # MOV ACC, NIL
                    self.write_state(dst, self.acc)
                elif src in [LEFT, UP, RIGHT, DOWN, ANY, LAST]:
                    if dst == ACC:
                        self.read_state(src, ACC_MOV)
                    else:
                        # MOV LEFT, RIGHT
                        # MOV RIGHT, DOWN
                        # MOV DOWN, ANY
                        self.read_state(src, dst)
                else:
                    raise Exception('illegal instruction: "{}"'.format(instruction))
            elif opcode == ADD:
                val = parts.pop(0)
                if val in [LEFT, UP, RIGHT, DOWN, ANY, LAST]:
                    # read from one of our ports and add to acc register
                    trace('instruction "{}" adding from {} to acc'.format(instruction, val))
                    self.read_state(val, ACC_ADD)
                elif is_number(val):
                    val = int(val)
                    trace('add instruction, val is {}'.format(val))
                    self.add(val)
                else:
                    raise Exception('illegal instruction: "{}"'.format(instruction))
            elif opcode == SUB:
                val = parts.pop(0)
                if val in [LEFT, UP, RIGHT, DOWN, ANY, LAST]:
                    trace('instruction "{}" subtracting from {} to acc'.format(instruction, val))
                    self.read_state(val, ACC_SUB)
                elif is_number(val):
                    val = int(val)
                    trace('sub instruction, val is {}'.format(val))
                    self.sub(val)
                else:
                    raise Exception('illegal instruction: "{}"'.format(instruction))
            elif opcode == NEG:
                self.acc = -self.acc
            elif opcode == SAV:
                self.bak = self.acc
            elif opcode == SWP:
                self.acc, self.bak = self.bak, self.acc
            elif opcode == JMP:
                label = parts.pop(0)
                self.check_label(label)
                # HACK: we will increment PC after the if block
                self.pc = self.labels[label] - 1
            elif opcode == JEZ:
                label = parts.pop(0)
                self.check_label(label)
                if self.acc == 0:
                    # HACK: we will increment PC after the if block
                    self.pc = self.labels[label] - 1
            elif opcode == JNZ:
                label = parts.pop(0)
                self.check_label(label)
                if self.acc != 0:
                    # HACK: we will increment PC after the if block
                    self.pc = self.labels[label] - 1
            elif opcode == JGZ:
                label = parts.pop(0)
                self.check_label(label)
                if self.acc > 0:
                    # HACK: we will increment PC after the if block
                    self.pc = self.labels[label] - 1
            elif opcode == JLZ:
                label = parts.pop(0)
                self.check_label(label)
                if self.acc < 0:
                    # HACK: we will increment PC after the if block
                    self.pc = self.labels[label] - 1
            elif opcode == JRO:
                offset = int(parts.pop(0))
                # HACK: we will increment PC after the if block
                # TODO: handle wrap-around
                self.pc += offset - 1
            else:
                raise Exception('unknown opcode at line {} for instruction "{}'.format(self.pc, instruction))
            # increment program counter so long as:
            # we are in the RUN state
            # we did not just execute a jump instruction
            if self.state == RUN and opcode not in [JMP, JNZ, JEZ, JGZ, JLZ, JRO]:
                self.pcinc()

    def pcinc(self):
        debug('{} incrementing from {}'.format(self.name, self.pc))
        self.pc += 1
        self.pc %= len(self.instructions)
        # TODO: while not_empty(self.instruction[self.pc])
        # in order to skip over comments and blank lines in the code
        while self.instructions[self.pc].strip() == '':
            self.pc += 1
            self.pc %= len(self.instructions)
        debug('{} just incremented to {}'.format(self.name, self.pc))

    def bounds_check(self):
        if self.acc > 999:
            self.acc = 999
        if self.acc < -999:
            self.acc = -999

    def add(self, value):
        self.acc += value
        self.bounds_check()

    def sub(self, value):
        self.add(-value)

    def set_acc(self, value):
        self.acc = value
        self.bounds_check()

    def str_instructions(self):
        width = 20
        res = [''.ljust(width)+'|'] * 15
        for idx, instruction in enumerate(self.instructions):
            if idx == self.pc:
                res[idx] = ('*'+instruction).ljust(width) + '|'
            else:
                res[idx] = instruction.ljust(width) + '|'

        def quad(title, value, location, idx):
            location[idx] += title.ljust(4) + '|'
            location[idx + 1] += str(value).ljust(4) + '|'
            location[idx + 2] += '-' * 5

        # acc
        quad('ACC', str(self.acc), res, 0)
        # bak
        quad('BAK', str(self.bak), res, 3)
        # last
        quad('LAST', 'todo', res, 6)
        # mode
        quad('MODE', self.state, res, 9)
        # idle
        quad('IDLE', 'todo', res, 12)
        return res

    def __str__(self):
        # TODO: create an array of size 15 with | at the end of each line
        # then put the necessary values (acc, bak, state, etc)
        # at the ends of the appropriate lines, and be sure to pad everything out
        # use a helper to return just the array
        # and use .join('\n') for the actual __str__ method
        res = self.str_instructions()
        return self.name + '\n' + '\n'.join(res)


if __name__ == '__main__':
    chip1 = AssemblyChip()
    chip1.parse('''add 1
    mov acc, right
    add right, acc
    ''')

    chip2 = AssemblyChip()
    chip2.parse('''add left, acc
    move acc, right
    ''')

    chip1.right = chip2
    chip2.left = chip1

    while True:
        print()
        print(chip1)
        print('-' * 25)
        print(chip2)
        print('-' * 25)
        val = input('enter to continue, q+enter to exit')
        if val == 'q':
            break
        chip1.run()
        chip2.run()
        AssemblyChip.global_pc += 1

# done
