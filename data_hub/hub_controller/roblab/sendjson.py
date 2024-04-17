import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import json

class GoalPublisher(Node):
    def __init__(self):
        super().__init__('goal_pose_publisher')
        self.publisher_ = self.create_publisher(PoseStamped, 'goal_pose', 10)
        # 注意：我们不再在构造函数中创建定时器来周期性调用publish_goal_pose

    def publish_goal_pose(self, goal_json):
        # 解析JSON数据
        goal_dict = json.loads(goal_json)
        
        # 创建PoseStamped消息
        goal_pose = PoseStamped()
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.header.frame_id = "map"  # 假设目标点是在地图坐标系下
        goal_pose.pose.position.x = goal_dict['position']['x']
        goal_pose.pose.position.y = goal_dict['position']['y']
        goal_pose.pose.position.z = goal_dict['position']['z']
        goal_pose.pose.orientation.x = goal_dict['orientation']['x']
        goal_pose.pose.orientation.y = goal_dict['orientation']['y']
        goal_pose.pose.orientation.z = goal_dict['orientation']['z']
        goal_pose.pose.orientation.w = goal_dict['orientation']['w']
        
        # 发布目标点
        self.publisher_.publish(goal_pose)
        self.get_logger().info('Publishing: "%s"' % goal_pose)

def main(args=None):
    rclpy.init(args=args)
    goal_publisher = GoalPublisher()
    
    # 示例JSON数据
    goal_json = '''
    {
      "position": {
        "x": 1.0,
        "y": 2.0,
        "z": 0.0
      },
      "orientation": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "w": 1.0
      }
    }
    '''
    
    # 直接调用publish_goal_pose函数，并传入目标点和朝向的JSON字符串
    goal_publisher.publish_goal_pose(goal_json)

    try:
        rclpy.spin_once(goal_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        goal_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

