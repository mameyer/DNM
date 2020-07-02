import time
from thunderborg.ThunderBorg import ThunderBorg
import math

class StepperControl:
    def __init__(self, i2c_address, max_power, holding_power):
        self.TB = ThunderBorg()
        self.TB.i2cAddress = i2c_address
        self.TB.Init()
        self.step = -1
        self.position = 0

        if not self.TB.foundChip:  # or not TB_z.foundChip:
            boards = ThunderBorg.ScanForThunderBorg()
            if len(boards) == 0:
                print("No ThunderBorg found, check you are attached..")
            else:
                for board in boards:
                    print("    %02X (%d)' % (board, board)")

            raise Exception("Board with i2c address %i not found" % i2c_address)

        self.max_power = max_power
        self.holding_power = holding_power

        # Order for stepping
        self.sequence = []
        self.init_sequence()

        # Order for stepping at holding power
        self.sequence_hold = []
        self.init_sequence_hold()

    def init_sequence(self):
        self.sequence = [
            [+self.max_power, +self.max_power],
            [+self.max_power, -self.max_power],
            [-self.max_power, -self.max_power],
            [-self.max_power, +self.max_power]
        ]

    def init_sequence_hold(self):
        self.sequence_hold = [
            [+self.holding_power, +self.holding_power],
            [+self.holding_power, -self.holding_power],
            [-self.holding_power, -self.holding_power],
            [-self.holding_power, +self.holding_power]
        ]

    def init_steps(self):
        if self.step == -1:
            drive = self.sequence[-1]
            self.TB.SetMotor1(drive[0])
            self.TB.SetMotor2(drive[1])
            self.step = 0
            time.sleep(0.5)

        self.position = 0

    def move(self, direction):
        # Wrap step when we reach the end of the sequence
        if self.step < 0:
            self.step = len(self.sequence) - 1
        elif self.step >= len(self.sequence):
            self.step = 0

        drive = self.sequence[self.step]
        self.TB.SetMotor1(drive[0])
        self.TB.SetMotor2(drive[1])

        self.step += direction
        self.position += direction

    def hold_position(self):
        # For the current step set the required holding drive values
        if self.step < len(self.sequence):
            drive = self.sequence_hold[self.step]
            self.TB.SetMotor1(drive[0])
            self.TB.SetMotor2(drive[1])

    def set_max_power(self, max_power):
        self.max_power = max_power
        self.init_sequence()

    def set_holding_power(self, holding_power):
        self.holding_power = holding_power
        self.init_sequence_hold()

    def stop(self):
        self.TB.MotorsOff()

    def reset_position(self):
        self.position = 0


class DrillControl:
    def __init__(self, max_power, holding_power):
        self.stepper_control_x = StepperControl(12, max_power, holding_power)
        self.stepper_control_y = StepperControl(11, max_power, holding_power)
        self.stepper_control_z = StepperControl(10, max_power, holding_power)

    def init_steps(self):
        self.stepper_control_x.init_steps()
        self.stepper_control_y.init_steps()
        self.stepper_control_z.init_steps()

    def set_max_power(self, max_power):
        self.stepper_control_x.set_max_power(max_power)
        self.stepper_control_y.set_max_power(max_power)
        self.stepper_control_z.set_max_power(max_power)

    def set_holding_power(self, holding_power):
        self.stepper_control_x.set_holding_power(holding_power)
        self.stepper_control_y.set_holding_power(holding_power)
        self.stepper_control_z.set_holding_power(holding_power)

    def stop(self):
        self.stepper_control_x.stop()
        self.stepper_control_y.stop()
        self.stepper_control_z.stop()

    def hold_position(self):
        self.stepper_control_x.hold_position()
        self.stepper_control_y.hold_position()
        self.stepper_control_z.hold_position()

    def reset_position(self):
        self.stepper_control_x.reset_position()
        self.stepper_control_y.reset_position()
        self.stepper_control_z.reset_position()

    def move(self, steps_x, steps_y, steps_z, step_delay):
        direction_x = 1
        if steps_x < 0:
            direction_x = -1
            steps_x *= -1

        direction_y = 1
        if steps_y < 0:
            direction_y = -1
            steps_y *= -1

        direction_z = 1
        if steps_z < 0:
            direction_z = -1
            steps_z *= -1

        max_steps = max([steps_x, steps_y, steps_z])
        print("max steps %i" % max_steps)

        # Loop through the max_steps
        for i in range(0, max_steps):
            if i < steps_x:
                self.stepper_control_x.move(direction_x)

            if i < steps_y:
                self.stepper_control_y.move(direction_y)

            if i < steps_z:
                self.stepper_control_z.move(direction_z)

            time.sleep(step_delay)

        self.hold_position()

    def arc(self, radius, target_angle, direction, mirror):
        angle = 0
        current_pos_x = radius
        current_pos_y = 0

        resolution = 360
        angle_diff = 360 / float(resolution)

        while angle < target_angle:
            print("angle=%d" % angle)
            angle_radians = math.radians(direction * angle)

            new_pos_x = math.cos(angle_radians) * radius
            new_pos_y = math.sin(angle_radians) * radius

            if mirror:
                new_pos_x *= -1
                new_pos_y *= -1

            print("  new pos: x=%d, y=%d" % (new_pos_x, new_pos_y))

            diff_x = new_pos_x - current_pos_x
            diff_y = new_pos_y - current_pos_y
            print("  diff: x=%d, y=%d" % (diff_x, diff_y))

            if abs(diff_x) >= 1:
                diff_x = int(math.ceil(diff_x))
                current_pos_x += diff_x
            else:
                diff_x = 0

            if abs(diff_y) >= 1:
                diff_y = int(math.ceil(diff_y))
                current_pos_y += diff_y
            else:
                diff_y = 0

            drill_control.move(diff_x, diff_y, 0, 0.005)
            angle += angle_diff


if __name__ == "__main__":
    drill_control = DrillControl(0.35, 0.05)
    drill_control.init_steps()
    drill_control.stop()
    time.sleep(2)

    drill_control.arc(100, 180, 1, False)
    drill_control.move(0, 400, 0, 0.001)
    drill_control.arc(100, 180, 1, False)
    drill_control.move(0, -400, 0, 0.001)
    drill_control.arc(100, 180, 1, False)
    drill_control.move(0, -100, 0, 0.001)
    drill_control.move(600, 0, 0, 0.001)
    drill_control.move(0, 100, 0, 0.001)

    #drill_control.set_max_power(0.225)
    #drill_control.move(0, 0, 600, 0.005)

    #drill_control.set_max_power(0.25)
    #drill_control.move(100, 100, 0, 0.001)
    #drill_control.move(0, 100, 0, 0.001)
    #drill_control.move(100, 0, 0, 0.001)
    #drill_control.move(-200, -200, 0, 0.001)

    #drill_control.set_max_power(0.225)
    #drill_control.move(0, 0, -600, 0.005)

    drill_control.stop()