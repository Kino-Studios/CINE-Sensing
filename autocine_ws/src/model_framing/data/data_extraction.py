import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import PolygonStamped, Point32
from cv_bridge import CvBridge
import cv2
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image as PILImage, ImageTk
import threading
from queue import Queue

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

workspace_root = os.path.join(project_root, 'autocine_ws', 'install')
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

try:
    from configs.user_params.constants import (
        ModelDetectionConstants, 
        UserRequestedParameters,
        RuleOfThirdsConstants
    )
except ImportError:
    class ModelDetectionConstants:
        CAMERA_IMAGE_TOPIC = '/camera/image_raw'
        BOUNDING_BOX_TOPIC = '/object_detection/bounding_box'
        IMAGE_ENCODING = 'bgr8'
        NUM_BOUNDING_BOX_POINTS = 4
        MODEL_PATH = os.path.expanduser('~/yolo_model.pt')
    
    class UserRequestedParameters:
        USER_OBJECT_ID = 11
    
    class RuleOfThirdsConstants:
        FRAME_WIDTH = 1152
        FRAME_HEIGHT = 648
        GRID_LINE_1_X = 384
        GRID_LINE_2_X = 768
        GRID_LINE_1_Y = 216
        GRID_LINE_2_Y = 432
        CORE_ANCHOR_POINTS = [
            (384, 216), (768, 216),
            (384, 432), (768, 432)
        ]


class DataExtractionNode(Node):
    def __init__(self, data_queue):
        super().__init__('data_extraction_node')
        self.data_queue = data_queue
        self.bridge = CvBridge()
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_subscriber = self.create_subscription(
            Image,
            ModelDetectionConstants.CAMERA_IMAGE_TOPIC,
            self.image_callback,
            qos_profile
        )
        
        self.bbox_subscriber = self.create_subscription(
            PolygonStamped,
            ModelDetectionConstants.BOUNDING_BOX_TOPIC,
            self.bbox_callback,
            qos_profile
        )
        
        self.current_image = None
        self.current_bbox = None
        self.image_lock = threading.Lock()
        
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                msg, 
                desired_encoding=ModelDetectionConstants.IMAGE_ENCODING
            )
            with self.image_lock:
                self.current_image = cv_image
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def bbox_callback(self, msg):
        try:
            if len(msg.polygon.points) >= 4:
                corners = []
                for point in msg.polygon.points[:4]:
                    corners.append([point.x, point.y])
                self.current_bbox = np.array(corners)
        except Exception as e:
            self.get_logger().error(f'Error processing bounding box: {str(e)}')
    
    def get_current_data(self):
        with self.image_lock:
            return self.current_image.copy() if self.current_image is not None else None, \
                   self.current_bbox.copy() if self.current_bbox is not None else None


class DataExtractionGUI:
    def __init__(self, root, ros_node):
        self.root = root
        self.ros_node = ros_node
        self.root.title("Data Extraction Tool")
        self.root.geometry("1152x648")
        
        self.data_records = []
        self.csv_file = None
        self.region_size = 100
        self.alignment_tolerance = 50
        self.capture_mode = "rule_of_thirds"
        
        self.setup_gui()
        self.update_display()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(control_frame, text="CSV Output File:").grid(row=0, column=0, padx=5, pady=5)
        self.csv_path_var = tk.StringVar(value="bounding_box_data.csv")
        ttk.Entry(control_frame, textvariable=self.csv_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Browse", command=self.browse_csv_file).grid(row=0, column=2, padx=5, pady=5)
        
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=3, padx=10, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="rule_of_thirds")
        ttk.Radiobutton(mode_frame, text="Rule of Thirds", variable=self.mode_var, 
                       value="rule_of_thirds", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Control", variable=self.mode_var, 
                       value="control", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        
        self.capture_button = ttk.Button(
            control_frame, 
            text="Capture Data Point", 
            command=self.capture_data,
            state=tk.NORMAL
        )
        self.capture_button.grid(row=0, column=4, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Save to CSV", command=self.save_to_csv).grid(row=0, column=5, padx=5, pady=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Ready", foreground="green")
        self.status_label.grid(row=1, column=0, columnspan=6, pady=5)
        
        alignment_info_frame = ttk.LabelFrame(control_frame, text="Alignment Guide", padding="5")
        alignment_info_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5)
        
        self.alignment_label = ttk.Label(alignment_info_frame, text="Move camera to align object center with grid intersection", foreground="blue")
        self.alignment_label.pack()
        
        self.mode_label = ttk.Label(alignment_info_frame, text="Current Mode: Rule of Thirds", foreground="green")
        self.mode_label.pack()
        
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        left_frame = ttk.LabelFrame(display_frame, text="With Rule of Thirds Framing", padding="5")
        left_frame.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas_with_grid = tk.Canvas(left_frame, width=640, height=360, bg="black")
        self.canvas_with_grid.pack()
        
        right_frame = ttk.LabelFrame(display_frame, text="Without Rule of Thirds Framing", padding="5")
        right_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas_without_grid = tk.Canvas(right_frame, width=640, height=360, bg="black")
        self.canvas_without_grid.pack()
        
        info_frame = ttk.LabelFrame(main_frame, text="Data Info", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.info_text = tk.Text(info_frame, height=8, width=100)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        
    def update_mode(self):
        self.capture_mode = self.mode_var.get()
        if self.capture_mode == "rule_of_thirds":
            self.mode_label.config(text="Current Mode: Rule of Thirds (Aligned)", foreground="green")
            self.alignment_label.config(text="Move camera to align object center with grid intersection", foreground="blue")
        else:
            self.mode_label.config(text="Current Mode: Control (Non-aligned)", foreground="orange")
            self.alignment_label.config(text="Capture data at any position (not aligned with grid)", foreground="orange")
    
    def browse_csv_file(self):
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path_var.set(filename)
    
    def draw_rule_of_thirds_grid(self, image):
        img_copy = image.copy()
        height, width = img_copy.shape[:2]
        
        grid_x1 = int(RuleOfThirdsConstants.GRID_LINE_1_X * width / RuleOfThirdsConstants.FRAME_WIDTH)
        grid_x2 = int(RuleOfThirdsConstants.GRID_LINE_2_X * width / RuleOfThirdsConstants.FRAME_WIDTH)
        grid_y1 = int(RuleOfThirdsConstants.GRID_LINE_1_Y * height / RuleOfThirdsConstants.FRAME_HEIGHT)
        grid_y2 = int(RuleOfThirdsConstants.GRID_LINE_2_Y * height / RuleOfThirdsConstants.FRAME_HEIGHT)
        
        cv2.line(img_copy, (grid_x1, 0), (grid_x1, height), (128, 128, 128), 1, cv2.LINE_AA)
        cv2.line(img_copy, (grid_x2, 0), (grid_x2, height), (128, 128, 128), 1, cv2.LINE_AA)
        cv2.line(img_copy, (0, grid_y1), (width, grid_y1), (128, 128, 128), 1, cv2.LINE_AA)
        cv2.line(img_copy, (0, grid_y2), (width, grid_y2), (128, 128, 128), 1, cv2.LINE_AA)
        
        anchor_scale_x = width / RuleOfThirdsConstants.FRAME_WIDTH
        anchor_scale_y = height / RuleOfThirdsConstants.FRAME_HEIGHT
        
        calculated_anchor_rects = self.calculate_anchor_rectangles()
        
        for cluster_id, (base_anchor_x, base_anchor_y) in enumerate(RuleOfThirdsConstants.CORE_ANCHOR_POINTS):
            anchor_rect = calculated_anchor_rects[cluster_id]
            
            region_x_min = int((base_anchor_x - self.region_size / 2) * anchor_scale_x)
            region_x_max = int((base_anchor_x + self.region_size / 2) * anchor_scale_x)
            region_y_min = int((base_anchor_y - self.region_size / 2) * anchor_scale_y)
            region_y_max = int((base_anchor_y + self.region_size / 2) * anchor_scale_y)
            
            cv2.rectangle(img_copy, (region_x_min, region_y_min), (region_x_max, region_y_max), 
                        (200, 200, 200), 1, cv2.LINE_AA)
            
            scaled_anchor_rect = anchor_rect.copy()
            scaled_anchor_rect[:, 0] *= anchor_scale_x
            scaled_anchor_rect[:, 1] *= anchor_scale_y
            
            for i in range(4):
                pt1 = tuple(scaled_anchor_rect[i].astype(int))
                pt2 = tuple(scaled_anchor_rect[(i + 1) % 4].astype(int))
                cv2.line(img_copy, pt1, pt2, (0, 0, 255), 2, cv2.LINE_AA)
            
            for corner in scaled_anchor_rect:
                px, py = corner.astype(int)
                size = 8
                cv2.line(img_copy, (px - size, py - size), (px + size, py + size), (0, 0, 255), 2, cv2.LINE_AA)
                cv2.line(img_copy, (px - size, py + size), (px + size, py - size), (0, 0, 255), 2, cv2.LINE_AA)
        
        if self.data_records:
            for record in self.data_records:
                px = int(record['x_px'] * anchor_scale_x)
                py = int(record['y_px'] * anchor_scale_y)
                cv2.circle(img_copy, (px, py), 3, (0, 100, 255), -1, cv2.LINE_AA)
        
        return img_copy
    
    def draw_bounding_box(self, image, bbox_corners, color=(0, 255, 0), thickness=2, show_alignment=True):
        if bbox_corners is None or len(bbox_corners) < 4:
            return image
        
        img_copy = image.copy()
        corners = bbox_corners.astype(int)
        
        for i in range(4):
            pt1 = tuple(corners[i])
            pt2 = tuple(corners[(i + 1) % 4])
            cv2.line(img_copy, pt1, pt2, color, thickness, cv2.LINE_AA)
        
        for corner in corners:
            cv2.circle(img_copy, tuple(corner), 5, color, -1)
        
        center = np.mean(corners, axis=0).astype(int)
        
        if show_alignment:
            cluster_id, nearest_anchor = self.get_region_for_point(center)
            dist_to_anchor = np.sqrt((center[0] - nearest_anchor[0])**2 + (center[1] - nearest_anchor[1])**2)
            
            if dist_to_anchor <= self.alignment_tolerance:
                center_color = (0, 255, 0)
                alignment_text = "ALIGNED"
            elif dist_to_anchor <= self.region_size / 2:
                center_color = (0, 255, 255)
                alignment_text = "CLOSE"
            else:
                center_color = (0, 0, 255)
                alignment_text = "MOVE CLOSER"
            
            cv2.circle(img_copy, tuple(center), 12, center_color, 3, cv2.LINE_AA)
            cv2.circle(img_copy, tuple(center), 8, (255, 0, 0), -1)
            
            cv2.putText(img_copy, alignment_text, (center[0] + 15, center[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, center_color, 2, cv2.LINE_AA)
            
            anchor_point = tuple(np.array(nearest_anchor).astype(int))
            cv2.line(img_copy, tuple(center), anchor_point, center_color, 1, cv2.LINE_AA)
            cv2.circle(img_copy, anchor_point, 5, center_color, 2, cv2.LINE_AA)
        else:
            cv2.circle(img_copy, tuple(center), 8, (255, 0, 0), -1)
        
        return img_copy
    
    def get_region_for_point(self, point):
        for idx, anchor in enumerate(RuleOfThirdsConstants.CORE_ANCHOR_POINTS):
            region_x_min = anchor[0] - self.region_size / 2
            region_x_max = anchor[0] + self.region_size / 2
            region_y_min = anchor[1] - self.region_size / 2
            region_y_max = anchor[1] + self.region_size / 2
            
            if (region_x_min <= point[0] <= region_x_max and 
                region_y_min <= point[1] <= region_y_max):
                return idx, anchor
        
        min_dist = float('inf')
        nearest_anchor = None
        anchor_index = -1
        
        for idx, anchor in enumerate(RuleOfThirdsConstants.CORE_ANCHOR_POINTS):
            dist = np.sqrt((point[0] - anchor[0])**2 + (point[1] - anchor[1])**2)
            if dist < min_dist:
                min_dist = dist
                nearest_anchor = anchor
                anchor_index = idx
        
        return anchor_index, nearest_anchor
    
    def calculate_anchor_rectangles(self):
        anchor_rects = {}
        for cluster_id in range(len(RuleOfThirdsConstants.CORE_ANCHOR_POINTS)):
            cluster_records = [r for r in self.data_records if r['cluster_id'] == cluster_id]
            if cluster_records:
                bbox_corners_list = []
                for record in cluster_records:
                    corners = np.array([
                        [record['bbox_x1'], record['bbox_y1']],
                        [record['bbox_x2'], record['bbox_y2']],
                        [record['bbox_x3'], record['bbox_y3']],
                        [record['bbox_x4'], record['bbox_y4']]
                    ])
                    bbox_corners_list.append(corners)
                
                if bbox_corners_list:
                    avg_corners = np.mean(bbox_corners_list, axis=0)
                    anchor_rects[cluster_id] = avg_corners
                else:
                    base_anchor = RuleOfThirdsConstants.CORE_ANCHOR_POINTS[cluster_id]
                    anchor_rects[cluster_id] = np.array([
                        [base_anchor[0] - 50, base_anchor[1] - 50],
                        [base_anchor[0] + 50, base_anchor[1] - 50],
                        [base_anchor[0] + 50, base_anchor[1] + 50],
                        [base_anchor[0] - 50, base_anchor[1] + 50]
                    ])
            else:
                base_anchor = RuleOfThirdsConstants.CORE_ANCHOR_POINTS[cluster_id]
                anchor_rects[cluster_id] = np.array([
                    [base_anchor[0] - 50, base_anchor[1] - 50],
                    [base_anchor[0] + 50, base_anchor[1] - 50],
                    [base_anchor[0] + 50, base_anchor[1] + 50],
                    [base_anchor[0] - 50, base_anchor[1] + 50]
                ])
        return anchor_rects
    
    def update_display(self):
        image, bbox = self.ros_node.get_current_data()
        
        if bbox is not None and image is not None:
            height, width = image.shape[:2]
            scale_x = RuleOfThirdsConstants.FRAME_WIDTH / width
            scale_y = RuleOfThirdsConstants.FRAME_HEIGHT / height
            
            scaled_bbox = bbox.copy()
            scaled_bbox[:, 0] *= scale_x
            scaled_bbox[:, 1] *= scale_y
            
            bbox_center = np.mean(scaled_bbox, axis=0)
            cluster_id, nearest_anchor = self.get_region_for_point(bbox_center)
            dist_to_anchor = np.sqrt((bbox_center[0] - nearest_anchor[0])**2 + (bbox_center[1] - nearest_anchor[1])**2)
            
            if dist_to_anchor <= self.alignment_tolerance:
                status_text = f"✓ ALIGNED with Region {cluster_id} (Distance: {dist_to_anchor:.1f}px)"
                status_color = "green"
            elif dist_to_anchor <= self.region_size / 2:
                status_text = f"→ Close to Region {cluster_id} (Distance: {dist_to_anchor:.1f}px) - Keep moving"
                status_color = "orange"
            else:
                status_text = f"✗ Far from alignment (Distance: {dist_to_anchor:.1f}px) - Move camera closer to grid"
                status_color = "red"
            
            self.alignment_label.config(text=status_text, foreground=status_color)
        elif bbox is None and image is not None:
            self.alignment_label.config(text="Waiting for object detection...", foreground="blue")
        
        if image is not None:
            canvas_width = 640
            canvas_height = 360
            height, width = image.shape[:2]
            scale = min(canvas_width / width, canvas_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized_image = cv2.resize(image, (new_width, new_height))
            
            img_with_grid = self.draw_rule_of_thirds_grid(resized_image)
            if bbox is not None:
                scaled_bbox = bbox * scale
                img_with_grid = self.draw_bounding_box(img_with_grid, scaled_bbox, color=(0, 255, 0), show_alignment=True)
            
            img_without_grid = resized_image.copy()
            if bbox is not None:
                scaled_bbox = bbox * scale
                img_without_grid = self.draw_bounding_box(img_without_grid, scaled_bbox, color=(0, 255, 0), show_alignment=False)
            
            img_with_grid_rgb = cv2.cvtColor(img_with_grid, cv2.COLOR_BGR2RGB)
            img_without_grid_rgb = cv2.cvtColor(img_without_grid, cv2.COLOR_BGR2RGB)
            
            pil_img_with = PILImage.fromarray(img_with_grid_rgb)
            pil_img_without = PILImage.fromarray(img_without_grid_rgb)
            
            photo_with = ImageTk.PhotoImage(image=pil_img_with)
            photo_without = ImageTk.PhotoImage(image=pil_img_without)
            
            self.canvas_with_grid.delete("all")
            self.canvas_with_grid.create_image(canvas_width//2, canvas_height//2, image=photo_with, anchor=tk.CENTER)
            self.canvas_with_grid.image = photo_with
            
            self.canvas_without_grid.delete("all")
            self.canvas_without_grid.create_image(canvas_width//2, canvas_height//2, image=photo_without, anchor=tk.CENTER)
            self.canvas_without_grid.image = photo_without
        
        self.root.after(33, self.update_display)
    
    def capture_data(self):
        image, bbox = self.ros_node.get_current_data()
        
        if image is None:
            messagebox.showwarning("No Image", "No image available")
            return
        
        if bbox is None:
            messagebox.showwarning("No Bounding Box", "No bounding box detected")
            return
        
        height, width = image.shape[:2]
        scale_x = RuleOfThirdsConstants.FRAME_WIDTH / width
        scale_y = RuleOfThirdsConstants.FRAME_HEIGHT / height
        
        scaled_bbox = bbox.copy()
        scaled_bbox[:, 0] *= scale_x
        scaled_bbox[:, 1] *= scale_y
        
        bbox_center = np.mean(scaled_bbox, axis=0)
        
        if self.capture_mode == "rule_of_thirds":
            cluster_id, base_anchor = self.get_region_for_point(bbox_center)
            dist_to_anchor = np.sqrt((bbox_center[0] - base_anchor[0])**2 + (bbox_center[1] - base_anchor[1])**2)
            
            if dist_to_anchor > self.alignment_tolerance:
                response = messagebox.askyesno(
                    "Not Aligned", 
                    f"Object center is {dist_to_anchor:.1f}px from nearest grid intersection.\n"
                    f"Capture anyway?"
                )
                if not response:
                    return
            
            calculated_anchor_rects = self.calculate_anchor_rectangles()
            anchor_rect = calculated_anchor_rects.get(cluster_id, None)
            
            if anchor_rect is None:
                anchor_rect = np.array([
                    [base_anchor[0] - 50, base_anchor[1] - 50],
                    [base_anchor[0] + 50, base_anchor[1] - 50],
                    [base_anchor[0] + 50, base_anchor[1] + 50],
                    [base_anchor[0] - 50, base_anchor[1] + 50]
                ])
            
            data_type = "rule_of_thirds"
        else:
            cluster_id = -1
            base_anchor = bbox_center
            
            anchor_rect = np.array([
                [bbox_center[0] - 50, bbox_center[1] - 50],
                [bbox_center[0] + 50, bbox_center[1] - 50],
                [bbox_center[0] + 50, bbox_center[1] + 50],
                [bbox_center[0] - 50, bbox_center[1] + 50]
            ])
            
            data_type = "control"
        
        anchor_center = np.mean(anchor_rect, axis=0)
        
        for i, corner in enumerate(scaled_bbox):
            anchor_corner = anchor_rect[i]
            relative_x = corner[0] - anchor_corner[0]
            relative_y = corner[1] - anchor_corner[1]
            
            record = {
                'data_type': data_type,
                'anchor_x': anchor_center[0],
                'anchor_y': anchor_center[1],
                'anchor_x1': anchor_rect[0, 0],
                'anchor_y1': anchor_rect[0, 1],
                'anchor_x2': anchor_rect[1, 0],
                'anchor_y2': anchor_rect[1, 1],
                'anchor_x3': anchor_rect[2, 0],
                'anchor_y3': anchor_rect[2, 1],
                'anchor_x4': anchor_rect[3, 0],
                'anchor_y4': anchor_rect[3, 1],
                'cluster_id': cluster_id,
                'x_px': corner[0],
                'y_px': corner[1],
                'relative_x': relative_x,
                'relative_y': relative_y,
                'bbox_x1': scaled_bbox[0, 0],
                'bbox_y1': scaled_bbox[0, 1],
                'bbox_x2': scaled_bbox[1, 0],
                'bbox_y2': scaled_bbox[1, 1],
                'bbox_x3': scaled_bbox[2, 0],
                'bbox_y3': scaled_bbox[2, 1],
                'bbox_x4': scaled_bbox[3, 0],
                'bbox_y4': scaled_bbox[3, 1],
                'center_x': bbox_center[0],
                'center_y': bbox_center[1],
                'timestamp': datetime.now().isoformat(),
            }
            self.data_records.append(record)
        
        rule_of_thirds_count = len([r for r in self.data_records if r.get('data_type') == 'rule_of_thirds'])
        control_count = len([r for r in self.data_records if r.get('data_type') == 'control'])
        
        self.status_label.config(
            text=f"Status: Captured {len(self.data_records)} data points (Rule of Thirds: {rule_of_thirds_count}, Control: {control_count})", 
            foreground="green"
        )
        
        self.update_info_text()
    
    def update_info_text(self):
        self.info_text.delete(1.0, tk.END)
        if self.data_records:
            rule_of_thirds_count = len([r for r in self.data_records if r.get('data_type') == 'rule_of_thirds'])
            control_count = len([r for r in self.data_records if r.get('data_type') == 'control'])
            
            self.info_text.insert(tk.END, f"Total data points: {len(self.data_records)}\n")
            self.info_text.insert(tk.END, f"Rule of Thirds: {rule_of_thirds_count} | Control: {control_count}\n")
            self.info_text.insert(tk.END, f"Last capture: {self.data_records[-1]['timestamp']}\n\n")
            
            self.info_text.insert(tk.END, "Last 5 records:\n")
            for record in self.data_records[-5:]:
                data_type = record.get('data_type', 'unknown')
                cluster_info = f"Cluster {record['cluster_id']}" if record['cluster_id'] >= 0 else "Control"
                self.info_text.insert(tk.END, 
                    f"[{data_type.upper()}] Corner ({record['x_px']:.1f}, {record['y_px']:.1f}) "
                    f"-> Anchor ({record['anchor_x']:.1f}, {record['anchor_y']:.1f}) "
                    f"[{cluster_info}]\n"
                )
        else:
            self.info_text.insert(tk.END, "No data captured yet\n")
    
    def save_to_csv(self):
        if not self.data_records:
            messagebox.showwarning("No Data", "No data to save")
            return
        
        csv_path = self.csv_path_var.get()
        if not csv_path:
            messagebox.showwarning("No File", "Specify CSV Path")
            return
        
        try:
            df = pd.DataFrame(self.data_records)
            df.to_csv(csv_path, index=False)
            self.status_label.config(
                text=f"Saved {len(self.data_records)} records to {csv_path}", 
                foreground="green"
            )
            messagebox.showinfo("Success", f"Data saved to {csv_path}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")


def main():
    rclpy.init()
    
    data_queue = Queue()
    ros_node = DataExtractionNode(data_queue)
    
    def spin_ros():
        rclpy.spin(ros_node)
    
    ros_thread = threading.Thread(target=spin_ros, daemon=True)
    ros_thread.start()
    
    root = tk.Tk()
    app = DataExtractionGUI(root, ros_node)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

