import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray, Pose
from cv_bridge import CvBridge
import json
import numpy as np
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import PointStamped
import rclpy.duration
import rclpy.parameter

FX = 554.0
FY = 554.0
CX = 320.0
CY = 240.0

class CoordTransformNode(Node):
    def __init__(self):
        super().__init__('coord_transform',
                         allow_undeclared_parameters=True,
                         automatically_declare_parameters_from_overrides=True)
        self.set_parameters([rclpy.parameter.Parameter(
            'use_sim_time', rclpy.parameter.Parameter.Type.BOOL, True)])

        self.bridge = CvBridge()
        self.latest_depth = None

        self.create_subscription(String, '/detected_chairs', self.chairs_callback, 10)
        self.create_subscription(Image, '/depth_camera/depth_image', self.depth_callback, 10)
        self.pub = self.create_publisher(PoseArray, '/empty_chairs_map', 10)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.get_logger().info('CoordTransformNode started')

    def depth_callback(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

    def chairs_callback(self, msg):
        chairs = json.loads(msg.data)
        if not chairs:
            return

        pose_array = PoseArray()
        pose_array.header.stamp = self.get_clock().now().to_msg()
        pose_array.header.frame_id = 'map'

        for chair in chairs:
            px, py = chair['cx'], chair['cy']

            if self.latest_depth is not None:
                h, w = self.latest_depth.shape[:2]
                if 0 <= px < w and 0 <= py < h:
                    depth = float(self.latest_depth[py, px])
                    if not np.isfinite(depth) or depth <= 0.1 or depth > 10.0:
                        depth = 2.0
                else:
                    depth = 2.0
            else:
                depth = 2.0

            x_cam = (px - CX) * depth / FX
            y_cam = (py - CY) * depth / FY
            z_cam = depth

            point = PointStamped()
            point.header.frame_id = 'camera_frame'
            point.header.stamp = rclpy.time.Time().to_msg()
            point.point.x = z_cam
            point.point.y = -x_cam
            point.point.z = -y_cam

            try:
                transformed = self.tf_buffer.transform(
                    point, 'map',
                    timeout=rclpy.duration.Duration(seconds=0.5)
                )
                pose = Pose()
                pose.position.x = transformed.point.x
                pose.position.y = transformed.point.y
                pose.position.z = 0.0
                pose.orientation.w = 1.0
                pose_array.poses.append(pose)
                self.get_logger().info(
                    f'Empty chair at map: ({transformed.point.x:.2f}, {transformed.point.y:.2f})'
                )
            except Exception as e:
                self.get_logger().warn(f'TF failed: {e}', throttle_duration_sec=2.0)

        if pose_array.poses:
            self.pub.publish(pose_array)

def main(args=None):
    rclpy.init(args=args)
    node = CoordTransformNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
