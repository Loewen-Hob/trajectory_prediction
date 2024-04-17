import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def ros_spin(node):
    rclpy.spin(node)
class StringSubscriber(Node):

    def __init__(self):
        super().__init__('string_subscriber')
        self.subscription = self.create_subscription(
            String,
            '/json',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.data = None

    def listener_callback(self, msg):
        # self.get_logger().info('I heard: "%s"' % msg.data)
        self.data = msg.data

def main(args=None):
    rclpy.init(args=args)
    string_subscriber = StringSubscriber()
    rclpy.spin(string_subscriber)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    print('over')
    string_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
