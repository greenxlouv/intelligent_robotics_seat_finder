# 🤖 YOLO 기반 객체 인식 및 지능형 빈 자리 탐색 안내 로봇

## 팀 정보
- **팀명**: sehr
- **팀원**: 이재린 (2371046)

## 프로젝트 설명
카페나 도서관 같은 실내 환경에서 로봇이 카메라로 빈 의자를 인식하고, 해당 위치를 지도 상에 표시하며, Nav2 자율주행으로 빈 자리까지 이동하는 시스템입니다.

## 시스템 구성
3개의 ROS2 노드로 구성:
- `chair_detector_node`: YOLOv8으로 사람 감지 + HSV 색상 필터로 의자 감지 -> 빈 의자 픽셀 좌표 퍼블리시
- `coord_transform_node`: Depth Camera + TF로 픽셀 좌표 -> 지도 2D 좌표 변환
- `seat_navigator_node`: Nav2 NavigateToPose Action으로 빈 의자까지 자율주행

## 실행 방법
```bash
ros2 launch seat_finder sim_cafe.launch.py
```

## AI 사용 여부 및 사용 내용
- **Claude Code**: 전반적인 코드 구현 보조, 디버깅, ROS2/Nav2 설정 문제 해결에 활용

## 참고 자료
- YOLOv8: https://docs.ultralytics.com/tasks/detect/
- Nav2: https://docs.nav2.org/
- ROS2 Humble: https://docs.ros.org/en/humble/
- Gazebo Fortress: https://gazebosim.org/docs/fortress
- ROS2 TF2: https://docs.ros.org/en/humble/Tutorials/Intermediate/Tf2/Tf2-Main.html
- OpenCV HSV: https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html

## YouTube 링크
https://www.youtube.com/watch?v=7s0CZ_deACs

## GitHub 링크
https://github.com/greenxlouv/intelligent_robotics_seat_finder

## License

See [LICENSE](LICENSE).
