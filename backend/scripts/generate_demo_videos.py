import os
import cv2
import numpy as np
import subprocess
from pathlib import Path

def draw_realistic_person(frame, x, y, scale=1.0, is_walking=True, frame_num=0):
    """
    Draws a realistic person silhouette with body, head, arms, and walking legs
    that is reliably detected by YOLOv8 as a person.
    """
    h = int(90 * scale)
    w = int(35 * scale)
    
    # Coordinates
    head_r = int(10 * scale)
    head_center = (x + w // 2, y + head_r + int(5 * scale))
    
    # Body color (dark tactical jacket)
    body_color = (40, 45, 55)
    skin_color = (130, 150, 180)
    pants_color = (30, 35, 40)
    
    # Head
    cv2.circle(frame, head_center, head_r, skin_color, -1)
    
    # Torso (Jacket)
    torso_top = head_center[1] + head_r
    torso_bottom = torso_top + int(40 * scale)
    torso_pts = np.array([
        [x + int(5 * scale), torso_top],
        [x + w - int(5 * scale), torso_top],
        [x + w - int(3 * scale), torso_bottom],
        [x + int(3 * scale), torso_bottom]
    ], np.int32)
    cv2.fillPoly(frame, [torso_pts], body_color)
    
    # Arms with swing motion
    swing = int(np.sin(frame_num * 0.4) * 8 * scale) if is_walking else 0
    cv2.line(frame, (x + int(5 * scale), torso_top + 5), (x + int(2 * scale) - swing, torso_bottom - 5), body_color, int(6 * scale))
    cv2.line(frame, (x + w - int(5 * scale), torso_top + 5), (x + w - int(2 * scale) + swing, torso_bottom - 5), body_color, int(6 * scale))
    
    # Legs (walking stride)
    leg_swing = int(np.sin(frame_num * 0.4) * 12 * scale) if is_walking else 0
    hip_left = (x + int(10 * scale), torso_bottom)
    hip_right = (x + w - int(10 * scale), torso_bottom)
    
    foot_left = (x + int(10 * scale) - leg_swing, y + h)
    foot_right = (x + w - int(10 * scale) + leg_swing, y + h)
    
    cv2.line(frame, hip_left, foot_left, pants_color, int(7 * scale))
    cv2.line(frame, hip_right, foot_right, pants_color, int(7 * scale))

def draw_realistic_vehicle(frame, x, y, scale=1.0):
    """
    Draws a realistic vehicle (SUV / Patrol Car) with chassis, cabin, wheels, and windows
    that is reliably detected by YOLOv8 as car/truck.
    """
    w = int(180 * scale)
    h = int(75 * scale)
    
    body_color = (50, 80, 110) # Tactical olive-slate
    window_color = (180, 195, 210)
    wheel_color = (25, 25, 25)
    rim_color = (160, 160, 160)
    
    # Lower Body / Chassis
    chassis_pts = np.array([
        [x, y + int(h * 0.45)],
        [x + w, y + int(h * 0.45)],
        [x + w - int(10 * scale), y + int(h * 0.85)],
        [x + int(10 * scale), y + int(h * 0.85)]
    ], np.int32)
    cv2.fillPoly(frame, [chassis_pts], body_color)
    
    # Cabin / Roof
    cabin_pts = np.array([
        [x + int(w * 0.25), y + int(h * 0.1)],
        [x + int(w * 0.70), y + int(h * 0.1)],
        [x + int(w * 0.85), y + int(h * 0.45)],
        [x + int(w * 0.15), y + int(h * 0.45)]
    ], np.int32)
    cv2.fillPoly(frame, [cabin_pts], body_color)
    
    # Windows
    front_win = np.array([
        [x + int(w * 0.52), y + int(h * 0.14)],
        [x + int(w * 0.68), y + int(h * 0.14)],
        [x + int(w * 0.80), y + int(h * 0.42)],
        [x + int(w * 0.52), y + int(h * 0.42)]
    ], np.int32)
    rear_win = np.array([
        [x + int(w * 0.28), y + int(h * 0.14)],
        [x + int(w * 0.48), y + int(h * 0.14)],
        [x + int(w * 0.48), y + int(h * 0.42)],
        [x + int(w * 0.20), y + int(h * 0.42)]
    ], np.int32)
    cv2.fillPoly(frame, [front_win], window_color)
    cv2.fillPoly(frame, [rear_win], window_color)
    
    # Wheels
    wheel_r = int(18 * scale)
    wheel1_center = (x + int(w * 0.25), y + int(h * 0.85))
    wheel2_center = (x + int(w * 0.75), y + int(h * 0.85))
    
    cv2.circle(frame, wheel1_center, wheel_r, wheel_color, -1)
    cv2.circle(frame, wheel1_center, int(wheel_r * 0.4), rim_color, -1)
    
    cv2.circle(frame, wheel2_center, wheel_r, wheel_color, -1)
    cv2.circle(frame, wheel2_center, int(wheel_r * 0.4), rim_color, -1)
    
    # Headlights
    cv2.circle(frame, (x + w - int(5 * scale), y + int(h * 0.55)), int(5 * scale), (100, 240, 255), -1)

def create_surveillance_background(width=1280, height=720):
    """
    Creates a realistic CCTV background of a border outpost with mountains, terrain, road, and fence.
    """
    bg = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Sky gradient (daylight surveillance tone)
    for i in range(int(height * 0.45)):
        ratio = i / (height * 0.45)
        color = [int(190 + 30 * ratio), int(205 + 25 * ratio), int(220 + 20 * ratio)]
        bg[i, :] = color
        
    # Mountains in distance
    mountain_pts = np.array([
        [0, int(height * 0.35)],
        [200, int(height * 0.22)],
        [450, int(height * 0.30)],
        [750, int(height * 0.18)],
        [1050, int(height * 0.28)],
        [width, int(height * 0.24)],
        [width, int(height * 0.45)],
        [0, int(height * 0.45)]
    ], np.int32)
    cv2.fillPoly(bg, [mountain_pts], (140, 155, 165))
    
    # Ground / Field (Earth / dry grass)
    for i in range(int(height * 0.45), height):
        ratio = (i - height * 0.45) / (height * 0.55)
        color = [int(90 - 20 * ratio), int(120 - 15 * ratio), int(135 - 20 * ratio)]
        bg[i, :] = color
        
    # Perimeter Border Road
    road_pts = np.array([
        [0, int(height * 0.65)],
        [width, int(height * 0.58)],
        [width, int(height * 0.78)],
        [0, int(height * 0.88)]
    ], np.int32)
    cv2.fillPoly(bg, [road_pts], (110, 115, 120))
    
    # Border Fence Posts & Mesh Line
    fence_y = int(height * 0.50)
    for x in range(30, width, 60):
        cv2.line(bg, (x, fence_y - 45), (x, fence_y + 10), (70, 75, 80), 3)
    cv2.line(bg, (0, fence_y - 40), (width, fence_y - 40), (80, 85, 90), 2)
    cv2.line(bg, (0, fence_y - 20), (width, fence_y - 20), (80, 85, 90), 2)
    cv2.line(bg, (0, fence_y), (width, fence_y), (80, 85, 90), 2)
    
    # Watchtower post on right side
    wt_x = width - 180
    wt_y = int(height * 0.30)
    cv2.rectangle(bg, (wt_x, wt_y), (wt_x + 60, wt_y + 160), (60, 65, 70), -1)
    cv2.rectangle(bg, (wt_x - 10, wt_y - 25), (wt_x + 70, wt_y), (50, 55, 60), -1)
    
    return bg

def generate_demo_video(output_path, scenario="incursion", num_frames=180, fps=25):
    """
    Generates a realistic surveillance video with moving targets and encodes to browser-ready H.264 MP4.
    """
    width, height = 1280, 720
    temp_raw_path = str(output_path).replace(".mp4", "_raw.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_raw_path, fourcc, fps, (width, height))
    
    base_bg = create_surveillance_background(width, height)
    
    for f in range(num_frames):
        frame = base_bg.copy()
        
        if scenario == "incursion":
            # Target 1: Intruder walking across the field from top-left into restricted zone
            # Starts at (120, 360) and walks southeast towards (600, 520)
            t = f / num_frames
            person_x = int(120 + t * 480)
            person_y = int(360 + t * 160)
            scale = 0.9 + t * 0.35 # Scales larger as target gets closer to camera
            draw_realistic_person(frame, person_x, person_y, scale=scale, is_walking=True, frame_num=f)
            
            # Target 2: Border security patrol vehicle moving along road
            if f > 30:
                v_t = (f - 30) / (num_frames - 30)
                veh_x = int(width - v_t * (width + 300))
                veh_y = int(height * 0.62)
                draw_realistic_vehicle(frame, veh_x, veh_y, scale=0.85)
                
        elif scenario == "patrol":
            # Target 1: Security guard stationary watch near watchtower
            draw_realistic_person(frame, width - 140, int(height * 0.44), scale=1.0, is_walking=False, frame_num=f)
            
            # Target 2: Patrol vehicle driving across perimeter road
            v_t = f / num_frames
            veh_x = int(-200 + v_t * (width + 400))
            veh_y = int(height * 0.65)
            draw_realistic_vehicle(frame, veh_x, veh_y, scale=0.95)
            
        # Add subtle CCTV timestamp and grain
        timestamp_str = f"2026-08-30 04:33:{f//fps:02d}.{(f%fps)*40:03d} UTC"
        cv2.putText(frame, timestamp_str, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
        cv2.putText(frame, "CAM-NP-01 | SECTOR 07 NORTH PERIMETER", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)
        
        out.write(frame)
        
    out.release()
    
    # Transcode to high-compatibility browser-ready H.264 via FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_raw_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_raw_path):
        os.remove(temp_raw_path)
        
    print(f"Generated demo video: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    demo_dir = Path(__file__).resolve().parent.parent / "demo_videos"
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    uploads_dir = Path(__file__).resolve().parent.parent / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Incursion Scenario
    incursion_demo = demo_dir / "demo_border_incursion.mp4"
    generate_demo_video(incursion_demo, scenario="incursion", num_frames=150, fps=25)
    
    # 2. Patrol Scenario
    patrol_demo = demo_dir / "demo_perimeter_patrol.mp4"
    generate_demo_video(patrol_demo, scenario="patrol", num_frames=150, fps=25)
    
    # Copy to uploads as default footage for immediate playback
    import shutil
    shutil.copy(incursion_demo, uploads_dir / "demo_border_incursion.mp4")
    shutil.copy(patrol_demo, uploads_dir / "demo_perimeter_patrol.mp4")
    print("Demo videos successfully initialized.")
