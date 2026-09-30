import sys
import math
import select
import termios
import tty

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


class HuskyKeyboardControl(Node):

    def __init__(self):
        super().__init__('husky_keyboard_control')

        self.cmd_pub = self.create_publisher(
            Twist,
            '/a200_0000/cmd_vel',
            10
        )

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/a200_0000/sensors/lidar2d_0/scan',
            self.scan_callback,
            10
        )

        self.front_distance = float('inf')

        self.normal_speed = 0.40
        self.slow_speed = 0.15
        self.reverse_speed = -0.25
        self.angular_speed = 0.70

        self.motion_state = 'STOP'

        self.timer = self.create_timer(
            0.05,
            self.control_loop
        )

        print()
        print("================================")
        print("      HUSKY KLAVYE KONTROL")
        print("================================")
        print("W : Ileri")
        print("S : Geri")
        print("A : Sola don")
        print("D : Saga don")
        print("SPACE : Dur")
        print("Q : Programdan cik")
        print()
        print("Mesafe > 1.0 m  : Normal hiz")
        print("0.5 - 1.0 m     : Yavas hiz")
        print("Mesafe <= 0.5 m : TAM DUR")
        print("================================")
        print()


    def scan_callback(self, msg):

        distances = []

        # Robotun onundeki +-10 derecelik LiDAR alani
        front_angle = math.radians(10)

        for i, distance in enumerate(msg.ranges):

            angle = msg.angle_min + i * msg.angle_increment

            if abs(angle) <= front_angle:

                if (
                    math.isfinite(distance)
                    and msg.range_min <= distance <= msg.range_max
                ):
                    distances.append(distance)

        if distances:
            self.front_distance = min(distances)
        else:
            self.front_distance = float('inf')


    def publish_motion(self, linear_x=0.0, angular_z=0.0):

        twist = Twist()

        twist.linear.x = float(linear_x)
        twist.angular.z = float(angular_z)

        self.cmd_pub.publish(twist)


    def control_loop(self):

        # ILERI
        if self.motion_state == 'FORWARD':

            if self.front_distance <= 0.50:

                self.publish_motion(0.0, 0.0)

                print(
                    f"\rDUR | Engel: {self.front_distance:.2f} m        ",
                    end='',
                    flush=True
                )

            elif self.front_distance <= 1.00:

                self.publish_motion(
                    self.slow_speed,
                    0.0
                )

                print(
                    f"\rYAVAS | Engel: {self.front_distance:.2f} m | "
                    f"Hiz: {self.slow_speed:.2f} m/s        ",
                    end='',
                    flush=True
                )

            else:

                self.publish_motion(
                    self.normal_speed,
                    0.0
                )

                if math.isfinite(self.front_distance):
                    distance_text = f"{self.front_distance:.2f} m"
                else:
                    distance_text = "Engel yok"

                print(
                    f"\rILERI | Engel: {distance_text} | "
                    f"Hiz: {self.normal_speed:.2f} m/s        ",
                    end='',
                    flush=True
                )


        # GERI
        elif self.motion_state == 'BACKWARD':

            self.publish_motion(
                self.reverse_speed,
                0.0
            )

            print(
                "\rGERI                               ",
                end='',
                flush=True
            )


        # SOL
        elif self.motion_state == 'LEFT':

            self.publish_motion(
                0.0,
                self.angular_speed
            )

            print(
                "\rSOLA DON                           ",
                end='',
                flush=True
            )


        # SAG
        elif self.motion_state == 'RIGHT':

            self.publish_motion(
                0.0,
                -self.angular_speed
            )

            print(
                "\rSAGA DON                           ",
                end='',
                flush=True
            )


        # DUR
        else:

            self.publish_motion(
                0.0,
                0.0
            )


    def handle_key(self, key):

        if key.lower() == 'w':
            self.motion_state = 'FORWARD'

        elif key.lower() == 's':
            self.motion_state = 'BACKWARD'

        elif key.lower() == 'a':
            self.motion_state = 'LEFT'

        elif key.lower() == 'd':
            self.motion_state = 'RIGHT'

        elif key == ' ':
            self.motion_state = 'STOP'


def get_key():

    tty.setraw(sys.stdin.fileno())

    ready, _, _ = select.select(
        [sys.stdin],
        [],
        [],
        0.05
    )

    if ready:
        return sys.stdin.read(1)

    return None


def main(args=None):

    rclpy.init(args=args)

    node = HuskyKeyboardControl()

    old_settings = termios.tcgetattr(
        sys.stdin
    )

    try:

        while rclpy.ok():

            rclpy.spin_once(
                node,
                timeout_sec=0.01
            )

            key = get_key()

            if key is None:
                continue

            if key.lower() == 'q':
                break

            node.handle_key(key)

    except KeyboardInterrupt:
        pass

    finally:

        node.motion_state = 'STOP'
        node.publish_motion(0.0, 0.0)

        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            old_settings
        )

        node.destroy_node()
        rclpy.shutdown()

        print("\nProgram kapatildi.")


if __name__ == '__main__':
    main()