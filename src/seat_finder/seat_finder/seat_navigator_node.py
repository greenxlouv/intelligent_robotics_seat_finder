import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseArray, Twist
from nav2_msgs.action import NavigateToPose
import rclpy.parameter

class SeatNavigatorNode(Node):
    def __init__(self):
        super().__init__('seat_navigator')
        self.set_parameters([rclpy.parameter.Parameter(
            'use_sim_time', rclpy.parameter.Parameter.Type.BOOL, True)])

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.create_subscription(PoseArray, '/empty_chairs_map', self.chairs_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.is_navigating = False
        self.is_rotating = False
        self.create_timer(0.1, self.rotate_timer)
        self.get_logger().info('SeatNavigatorNode started')

    def rotate_timer(self):
        if not self.is_navigating and not self.is_rotating:
            # 빈 의자 못 찾으면 회전하면서 탐색
            twist = Twist()
            twist.angular.z = 0.3
            self.cmd_vel_pub.publish(twist)

    def chairs_callback(self, msg):
        if self.is_navigating or not msg.poses:
            return

        # 회전 멈추고 이동
        self.cmd_vel_pub.publish(Twist())
        
        target = msg.poses[0]
        self.get_logger().info(
            f'Navigating to empty chair: ({target.position.x:.2f}, {target.position.y:.2f})'
        )
        self.send_goal(target)

    def send_goal(self, pose):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose = pose

        self._action_client.wait_for_server()
        self.is_navigating = True
        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected!')
            self.is_navigating = False
            return
        self.get_logger().info('Goal accepted! Navigating...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        self.get_logger().info('Reached empty chair! Navigation complete.')
        self.is_navigating = False
        # 도착 후 다시 회전하면서 탐색

def main(args=None):
    rclpy.init(args=args)
    node = SeatNavigatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()