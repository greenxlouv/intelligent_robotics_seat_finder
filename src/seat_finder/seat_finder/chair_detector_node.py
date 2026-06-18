import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import json
from ultralytics import YOLO

class ChairDetector(Node):
    def __init__(self):
        super().__init__('chair_detector')
        self.bridge = CvBridge()
        self.model = YOLO('yolov8n.pt')

        # 카페 의자 픽셀 좌표 (SDF 기준 고정 위치, 나중에 depth로 변환)
        # 테이블당 4개 의자, 4개 테이블 = 16개
        # 일단 비워두고 런타임에 색상으로 감지

        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.create_subscription(Image, '/depth_camera/depth_image', self.depth_callback, 10)

        self.pub = self.create_publisher(String, '/detected_chairs', 10)
        self.latest_depth = None
        self.get_logger().info('ChairDetector node started')

    def depth_callback(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

    def image_callback(self, msg):
        if not hasattr(self, 'frame_count'):
            self.frame_count = 0
        self.frame_count += 1
        if self.frame_count % 5 != 0:
            return
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # 1. YOLO로 person 감지
        results = self.model(frame, verbose=False, conf=0.3)[0]
        persons = []
        for box in results.boxes:
            cls_name = self.model.names[int(box.cls[0])]
            if cls_name == 'person':
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                persons.append({'cx': (x1+x2)//2, 'cy': (y1+y2)//2,
                                 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})

        # 2. 색상으로 의자 감지 (갈색/베이지 계열)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 갈색 범위
        lower = np.array([95, 100, 100])
        upper = np.array([115, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        # 노이즈 제거
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        chairs = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:  # 너무 작은 건 무시
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w//2, y + h//2
            chairs.append({'cx': cx, 'cy': cy, 'x1': x, 'y1': y, 'x2': x+w, 'y2': y+h})

        # 3. 빈 의자 판별
        empty_chairs = []
        for chair in chairs:
            occupied = False
            for person in persons:
                if (chair['x1'] < person['cx'] < chair['x2'] and
                        chair['y1'] < person['cy'] < chair['y2']):
                    occupied = True
                    break
            if not occupied:
                empty_chairs.append({'cx': chair['cx'], 'cy': chair['cy']})

        # 4. 시각화
        for chair in chairs:
            cv2.rectangle(frame, (chair['x1'], chair['y1']),
                          (chair['x2'], chair['y2']), (0, 255, 0), 2)
        for person in persons:
            cv2.rectangle(frame, (person['x1'], person['y1']),
                          (person['x2'], person['y2']), (0, 0, 255), 2)
        for ec in empty_chairs:
            cv2.circle(frame, (ec['cx'], ec['cy']), 10, (255, 0, 0), -1)

        cv2.imshow('ChairDetector', frame)
        cv2.waitKey(1)

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