import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import json
from ultralytics import YOLO


class ChairDetector(Node):
    def __init__(self):
        super().__init__('chair_detector')
        self.bridge = CvBridge()
        self.model = YOLO('yolov8n.pt')  # 첫 실행 시 자동 다운로드

        # RGB 카메라 구독
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)

        # 빈 의자 정보 퍼블리시 (픽셀 좌표)
        self.pub = self.create_publisher(String, '/detected_chairs', 10)

        self.get_logger().info('ChairDetector node started')

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        # 이미지 저장 (한 번만)
        if not hasattr(self, 'saved'):
            cv2.imwrite('/tmp/camera_view.png', frame)
            self.saved = True
            self.get_logger().info('Image saved to /tmp/camera_view.png')
        results = self.model(frame, verbose=False, conf=0.1)[0]


        # 디버깅: 모든 감지 결과 출력
        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])
            self.get_logger().info(f'detected: {cls_name} ({conf:.2f})')

        chairs = []

        chairs = []
        persons = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            if cls_name == 'chair':
                chairs.append({'cx': cx, 'cy': cy, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
            elif cls_name == 'person':
                persons.append({'cx': cx, 'cy': cy, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})

        # 빈 의자 판별: 사람과 겹치지 않는 의자
        empty_chairs = []
        for chair in chairs:
            occupied = False
            for person in persons:
                # 사람 중심이 의자 박스 안에 있으면 occupied
                if (chair['x1'] < person['cx'] < chair['x2'] and
                        chair['y1'] < person['cy'] < chair['y2']):
                    occupied = True
                    break
            if not occupied:
                empty_chairs.append({'cx': chair['cx'], 'cy': chair['cy']})

        # 시각화
        for chair in chairs:
            cv2.rectangle(frame, (chair['x1'], chair['y1']), (chair['x2'], chair['y2']), (0, 255, 0), 2)
        for person in persons:
            cv2.rectangle(frame, (person['x1'], person['y1']), (person['x2'], person['y2']), (0, 0, 255), 2)
        for ec in empty_chairs:
            cv2.circle(frame, (ec['cx'], ec['cy']), 10, (255, 0, 0), -1)

        cv2.imshow('ChairDetector', frame)
        cv2.waitKey(1)

        # 퍼블리시
        msg_out = String()
        msg_out.data = json.dumps(empty_chairs)
        self.pub.publish(msg_out)

        self.get_logger().info(
            f'chairs: {len(chairs)}, persons: {len(persons)}, empty: {len(empty_chairs)}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ChairDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
