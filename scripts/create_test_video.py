import os
import cv2
import numpy as np
from pathlib import Path

def generate_sample_surveillance_video(
    output_path: str = "data/uploads/sample_border_surveillance.mp4",
    width: int = 640,
    height: int = 480,
    fps: int = 20,
    duration_seconds: int = 8,
):
    """
    Generates a synthetic surveillance test video containing:
    1. Realistic textured border terrain background (fence lines, watchtower demarcations)
    2. A moving figure / pedestrian traversing from North across the border line and loitering.
    3. Moving vehicle in lower sector.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = fps * duration_seconds
    print(f"Generating synthetic test surveillance video: {output_path} ({total_frames} frames)...")

    # Base background (Night-vision / thermal tint style surveillance terrain)
    bg = np.zeros((height, width, 3), dtype=np.uint8)
    bg[:] = (35, 45, 30) # Dark olive-gray terrain

    # Draw border fence line
    cv2.line(bg, (0, int(height * 0.5)), (width, int(height * 0.5)), (80, 110, 90), 2)
    for fx in range(20, width, 40):
        cv2.line(bg, (fx, int(height * 0.45)), (fx, int(height * 0.55)), (70, 95, 80), 2)

    # Draw watchtower outline in background
    cv2.rectangle(bg, (520, 80), (590, 200), (50, 70, 60), 2)
    cv2.putText(bg, "WATCHTOWER 04", (510, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 130, 110), 1)

    for i in range(total_frames):
        frame = bg.copy()
        time_sec = i / fps

        # Simulate camera OSD (On-Screen Display)
        cv2.putText(frame, f"CAM-NP-01 | SECTOR 4 NORTH | {time_sec:05.2f}s", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 220, 200), 1)

        # Draw a moving intruder figure moving from top (y=100) down across fence (y=240) into buffer zone
        # Position updates over time
        progress = i / total_frames
        person_x = int(180 + progress * 200) # Moves diagonally right
        person_y = int(100 + progress * 260) # Moves downward across border fence

        # Draw realistic humanoid silhouette (head, torso, legs)
        # Head
        cv2.circle(frame, (person_x, person_y - 25), 8, (220, 220, 220), -1)
        # Torso
        cv2.rectangle(frame, (person_x - 10, person_y - 17), (person_x + 10, person_y + 12), (180, 180, 180), -1)
        # Legs
        leg_offset = int(np.sin(i * 0.8) * 4)
        cv2.line(frame, (person_x - 5, person_y + 12), (person_x - 7 + leg_offset, person_y + 32), (160, 160, 160), 3)
        cv2.line(frame, (person_x + 5, person_y + 12), (person_x + 7 - leg_offset, person_y + 32), (160, 160, 160), 3)

        # Vehicle moving horizontally across bottom
        if time_sec > 2.0:
            car_x = int((time_sec - 2.0) * 80)
            if car_x < width + 50:
                cv2.rectangle(frame, (car_x, 400), (car_x + 70, 440), (140, 140, 160), -1)
                cv2.circle(frame, (car_x + 15, 440), 6, (40, 40, 40), -1)
                cv2.circle(frame, (car_x + 55, 440), 6, (40, 40, 40), -1)

        out.write(frame)

    out.release()
    print(f"Test video generated successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_sample_surveillance_video()
