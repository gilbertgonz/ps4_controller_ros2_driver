import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from pyPS4Controller.event_mapping.DefaultMapping import DefaultMapping
import os
import struct
import time

class PS4Publisher(Node):
    def __init__(self):
        super().__init__("ps4_controller_node")

        event_format=None
        self.stop = False
        self.is_connected = False
        self._file = None
        self.event = None 
        self.interface = "/dev/input/js0"
        self.connecting_using_ds4drv = False
        self.event_format = event_format if event_format else "3Bh2b"
        self.event_definition = DefaultMapping

        self.event_size = struct.calcsize(self.event_format)
        self.event_history = []

        # ROS2 stuff
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.publish_call = self.create_timer(1/50, self.publish_data)
        self.get_logger().info("ps4 controller node started")

    def publish_data(self, on_sequence=None):
        if not self.is_connected:
            self.wait_for_interface()
        try:
            self._file = open(self.interface, "rb")
            self.event = self.read_events()
            if on_sequence is None:
                on_sequence = []
            special_inputs_indexes = [0] * len(on_sequence)
            while not self.stop and self.event:
                '''
                Overflow: TUPLE (value, type_id, button_id)

                L3 up-down:      (-32767:32767, 2, 1)
                L3 left-right:   (-32767:32767, 2, 0)

                R3 up-down:      (-32767:32767, 2, 4)
                R3 left-right:   (-32767:32767, 2, 3)

                up arrow:        (0:-32767, 2, 7)
                down arrow:      (0:32767, 2, 7)
                right arrow:     (0:32767, 2, 6)
                left arrow:      (0:-32767, 2, 6)

                x button:        (0:1, 1, 0)
                circle button:   (0:1, 1, 1)
                triangle button: (0:1, 1, 2)
                square button:   (0:1, 1, 3)
                
                L1 button:       (0:1, 1, 4)
                R1 button:       (0:1, 1, 5)

                L2:              (-32767:32767, 2, 2)
                                 (0:1, 1, 6)
                R2:              (-32767:32767, 2, 5)
                                 (0:1, 1, 7)

                share:          (0:1, 1, 8)
                option:         (0:1, 1, 9)
                ps button:      (0:1, 1, 10)
                '''

                (value, type_id, button_id) = self.unpack()
                thresh = 0.05

                if type_id == 1:
                    if button_id == 0:
                        print(f"x button: {value}")
                    if button_id == 1:
                        print(f"circle button: {value}")
                    if button_id == 2:
                        print(f"triangle button: {value}")
                    if button_id == 3:
                        print(f"square button: {value}")
                    if button_id == 4:
                        print(f"L1 button: {value}")
                    if button_id == 5:
                        print(f"R1 button: {value}")
                    if button_id == 6:
                        print(f"L2 release: {value}")
                    if button_id == 7:
                        print(f"R2 release: {value}")
                    if button_id == 8:
                        print(f"share: {value}")
                    if button_id == 9:
                        print(f"option: {value}")
                    if button_id == 10:
                        print(f"ps button: {value}")

                if type_id == 2:
                    
                    # L3 left-right
                    if button_id == 0:
                        value = self.map_value(value, -32767, 32767, -1.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"L3 left-right: {value}")

                    # L3 up-down
                    if button_id == 1:
                        value = self.map_value(value, 32767, -32767, -1.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"L3 up-down: {value}")

                    # L2
                    if button_id == 2:
                        value = self.map_value(value, -32767, 32767, 0.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"L2: {value}")

                    # R3 left-right
                    if button_id == 3:
                        value = self.map_value(value, -32767, 32767, -1.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"R3 left-right: {value}")

                    # R3 up-down
                    if button_id == 4:
                        value = self.map_value(value, 32767, -32767, -1.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"R3 up-down: {value}")

                    # R2
                    if button_id == 5:
                        value = self.map_value(value, -32767, 32767, 0.0, 1.0)
                        if -thresh <= value <= thresh:
                            value = 0.0
                        print(f"R2: {value}")

                    # right-left arrow
                    if button_id == 6:
                        print(f"right-left arrow: {value}")

                    # up-down arrow
                    if button_id == 7:
                        print(f"up-down arrow: {value}")
                
                twist_msg = Twist()
                # twist_msg.header.stamp = self.get_clock().now().to_msg()
                twist_msg.linear.x = 0.0
                twist_msg.linear.y = 0.0
                twist_msg.linear.z = 0.0
                twist_msg.angular.x = 0.0
                twist_msg.angular.y = 0.0
                twist_msg.angular.z = 0.0
                self.pub.publish(twist_msg)

                for i, special_input in enumerate(on_sequence):
                    check = self.check_for(special_input["inputs"], self.event_history, special_inputs_indexes[i])
                    if len(check) != 0:
                        special_inputs_indexes[i] = check[0] + 1
                        special_input["callback"]()
                self.event = self.read_events()
        except KeyboardInterrupt:
            self.get_logger().info("\nExiting (Ctrl + C)")
            exit(1)

    def wait_for_interface(self, timeout=10):
        self.get_logger().info("Waiting for interface: {} to become available . . .".format(self.interface))
        for i in range(timeout):
            if os.path.exists(self.interface):
                self.get_logger().info("Successfully bound to: {}.".format(self.interface))
                self.is_connected = True
                return
            time.sleep(1)
        self.get_logger().error("Timeout({} sec). Interface not available.".format(timeout))
        exit(1)

    def read_events(self):
        try:
            return self._file.read(self.event_size)
        except IOError:
            self.get_logger().warn("Interface lost. Device disconnected?")
            exit(1)

    def check_for(self, sub, full, start_index):
        return [start for start in range(start_index, len(full) - len(sub) + 1) if
                sub == full[start:start + len(sub)]]

    def unpack(self):
        __event = struct.unpack(self.event_format, self.event)
        return (__event[3:])
    
    def map_value(self, value, in_min, in_max, out_min, out_max):
        return round((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, 2)

def main(args=None):
    rclpy.init(args=args)
    pub_node = PS4Publisher()
    rclpy.spin(pub_node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
