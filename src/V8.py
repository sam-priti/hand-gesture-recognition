import cv2
import mediapipe as mp
import numpy as np
import time
import tkinter as tk
from tkinter import scrolledtext, Button, Frame, Label, StringVar, OptionMenu
from datetime import datetime
import re

# Modified CustomText class with simplified syntax highlighting and line numbers
class CustomText(scrolledtext.ScrolledText):
    """Extension of ScrolledText that supports line numbers and simplified syntax highlighting"""
    def __init__(self, *args, **kwargs):
        scrolledtext.ScrolledText.__init__(self, *args, **kwargs)
        self.configure_tags()
        self.orig = self._w + "_orig"
        self.tk.call("rename", self._w, self.orig)
        self.tk.createcommand(self._w, self._proxy)
        
        # Create line numbers text widget
        self.line_numbers = tk.Text(args[0], width=4, padx=4, pady=4, takefocus=0,
                                   bd=0, background='#1F2430', foreground='#5C6773',
                                   highlightthickness=0, font=kwargs.get('font'))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Bind events for scrolling sync
        self.vbar['command'] = self.on_scrollbar
        
        # Update line numbers on first display
        self.update_line_numbers()
        
    def configure_tags(self):
        """Configure text tags for simplified syntax highlighting"""
        # Only configure for strings and conditionals
        self.tag_configure("string", foreground="#C2D94C")   # Lime for strings
        self.tag_configure("conditional", foreground="#FF8F40")  # Orange for conditionals
    
    def _proxy(self, *args):
        """Intercept widget commands"""
        cmd = (self.orig,) + args
        result = self.tk.call(cmd)
        
        if args[0] in ("insert", "replace", "delete") or args[0:2] == ("mark", "set"):
            self.highlight()
            self.update_line_numbers()
            
        return result
    
    def on_scrollbar(self, *args):
        """Handle scrollbar movement and sync line numbers"""
        self.yview(*args)
        self.line_numbers.yview(*args)
    
    def update_line_numbers(self):
        """Update the line numbers display"""
        # Get visible lines
        first_line = self.index("@0,0").split('.')[0]
        last_line = self.index(f"@0,{self.winfo_height()}").split('.')[0]
        
        # Clear existing line numbers
        self.line_numbers.delete("1.0", tk.END)
        
        # Calculate how many lines in the editor
        text_content = self.get("1.0", tk.END)
        num_lines = text_content.count('\n') + 1
        
        # Add line numbers
        for i in range(1, num_lines + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")
        
        # Sync scrolling position
        self.line_numbers.yview_moveto(self.yview()[0])
    
    def highlight(self):
        """Apply simplified syntax highlighting to the text"""
        content = self.get("1.0", tk.END)
        
        # Clear all tags
        for tag in ["string", "conditional"]:
            self.tag_remove(tag, "1.0", tk.END)
        
        # Conditional keywords
        conditional_keywords = ["if", "else", "elif", "for", "while", "try", "except"]
        
        # Highlight conditional keywords
        for keyword in conditional_keywords:
            start_index = "1.0"
            word_pattern = r'\b' + keyword + r'\b'
            
            while True:
                start_index = self.search(word_pattern, start_index, tk.END, regexp=True)
                if not start_index:
                    break
                
                end_index = f"{start_index}+{len(keyword)}c"
                self.tag_add("conditional", start_index, end_index)
                start_index = end_index
        
        # Highlight strings
        for string_pattern in [r'"[^"\\\n]*(?:\\.[^"\\\n]*)*"', r"'[^'\\\n]*(?:\\.[^'\\\n]*)*'"]:
            start_index = "1.0"
            while True:
                start_index = self.search(string_pattern, start_index, tk.END, regexp=True)
                if not start_index:
                    break
                    
                content = self.get(start_index, tk.END)
                match = re.match(string_pattern, content)
                if match:
                    end_index = f"{start_index}+{len(match.group(0))}c"
                    self.tag_add("string", start_index, end_index)
                    start_index = end_index
                else:
                    break

class HandyCodesApp:
    def __init__(self):
        # Initialize MediaPipe Hands module
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        
        # Define gesture-to-code mapping with expanded functions
        self.gesture_code_mapping = {
            "open_palm": 'print("Hello World")',
            "thumbs_up": 'x = 10\nprint("Variable x set to", x)',
            "victory": 'x = 10\nif x > 5:\n    print("x is greater than 5")',
            "pointing_index": 'for i in range(5):\n    print("Loop iteration", i)',
            "fist": 'print("Fist detected - Stopping execution")',
            "three_fingers": 'def greet(name):\n    print(f"Hello, {name}!")\n\ngreet("User")'
        }
        
        # App state variables
        self.generated_code = ""  # Stores all executed code dynamically
        self.execution_output = ""  # Stores execution output
        self.last_executed_time = time.time()
        self.gesture_cooldown = 1.0  # 1 second cooldown
        self.last_detected_gesture = None
        self.gesture_hold_time = 0.3  # Must hold a gesture for 0.3 seconds
        self.gesture_start_time = None
        self.displayed_gesture = ""
        self.camera_active = True
        self.selected_camera = 0  # Default to camera 0 instead of 1
        self.available_cameras = self.get_available_cameras()
        self.running = True  # Flag to control the camera loop
        
        # Initialize UI
        self.setup_ui()
        
    def get_available_cameras(self):
        """Detect available camera devices"""
        available_cams = []
        for i in range(5):  # Check first 5 camera indexes
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cams.append(i)
                cap.release()
        return available_cams if available_cams else [0]  # Default to camera 0 if none found
    
    def setup_ui(self):
        """Set up the Tkinter user interface"""
        self.root = tk.Tk()
        self.root.title("HandyCodes - Gesture Code Editor")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.configure(background='#0F1419')  # Set dark background for the app
        
        # Main frame
        main_frame = Frame(self.root, bg='#0F1419')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top controls frame
        controls_frame = Frame(main_frame, bg='#0F1419')
        controls_frame.pack(fill="x", pady=5)
        
        # Camera selection
        Label(controls_frame, text="Camera:", bg='#0F1419', fg='#E6E1CF').pack(side="left", padx=5)
        self.camera_var = StringVar(self.root)
        self.camera_var.set(str(self.selected_camera))
        camera_menu = OptionMenu(controls_frame, self.camera_var, *[str(c) for c in self.available_cameras], 
                                command=self.change_camera)
        camera_menu.pack(side="left", padx=5)
        
        # Button frame
        button_frame = Frame(controls_frame, bg='#0F1419')
        button_frame.pack(side="right")
        
        # Buttons with improved styling
        button_style = {'bg': '#1F2430', 'fg': '#E6E1CF', 'padx': 10, 'pady': 5, 'bd': 0, 'relief': tk.RAISED}
        Button(button_frame, text="Run Code", command=self.run_code, **button_style).pack(side="left", padx=5)
        Button(button_frame, text="Clear Code", command=self.clear_code, **button_style).pack(side="left", padx=5)
        Button(button_frame, text="Save Code", command=self.save_code, **button_style).pack(side="left", padx=5)
        self.camera_button_text = StringVar()
        self.camera_button_text.set("Pause Camera")
        Button(button_frame, textvariable=self.camera_button_text, 
               command=self.toggle_camera, **button_style).pack(side="left", padx=5)
        
        # Middle section - Split view
        middle_frame = Frame(main_frame, bg='#0F1419')
        middle_frame.pack(fill="both", expand=True, pady=10)
        
        # Code editor - Left side
        code_frame = Frame(middle_frame, bg='#0F1419')
        code_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        Label(code_frame, text="Code Editor", font=("Arial", 12, "bold"), bg='#0F1419', fg='#E6E1CF').pack(anchor="w")
        
        # Code editor container to hold the line numbers and text editor
        editor_container = Frame(code_frame, bg='#0F1419')
        editor_container.pack(fill="both", expand=True)
        
        # Use our modified custom text widget with line numbers and simplified syntax highlighting
        self.code_editor = CustomText(editor_container, wrap=tk.NONE, 
                                    font=("Consolas", 12), width=60, height=20,
                                    bg="#0F1419", fg="#E6E1CF", insertbackground="#E6E1CF",
                                    selectbackground="#3D4752", selectforeground="#E6E1CF",
                                    bd=0, padx=5, pady=5)
        self.code_editor.pack(side=tk.RIGHT, fill="both", expand=True)
        
        # Output console - Right side
        output_frame = Frame(middle_frame, bg='#0F1419')
        output_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        Label(output_frame, text="Console Output", font=("Arial", 12, "bold"), bg='#0F1419', fg='#E6E1CF').pack(anchor="w")
        self.output_console = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                     font=("Consolas", 12), width=60, height=20,
                                                     bg="#131721", fg="#E6E1CF",
                                                     selectbackground="#3D4752", selectforeground="#E6E1CF",
                                                     bd=0, padx=10, pady=10)
        self.output_console.pack(fill="both", expand=True)
        self.output_console.config(state=tk.DISABLED)
        
        # Gesture guide - Bottom
        guide_frame = Frame(main_frame, bg='#0F1419')
        guide_frame.pack(fill="x", pady=5)
        
        Label(guide_frame, text="Gesture Guide:", font=("Arial", 11, "bold"), bg='#0F1419', fg='#E6E1CF').pack(anchor="w")
        gestures_text = ", ".join([f"{key}" for key in self.gesture_code_mapping.keys()])
        Label(guide_frame, text=gestures_text, font=("Arial", 10), bg='#0F1419', fg='#E6E1CF').pack(anchor="w")
        
        # Status bar - Very bottom
        self.status_var = StringVar()
        self.status_var.set("Camera Ready")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                         bg='#1F2430', fg='#E6E1CF')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Update code editor with initial content
        self.update_code_display()
    
    def change_camera(self, selection):
        """Change the selected camera"""
        self.selected_camera = int(selection)
        self.status_var.set(f"Switching to camera {self.selected_camera}...")
        
        # Need to restart the camera in the main loop
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            
        self.start_camera()
    
    def toggle_camera(self):
        """Toggle camera on/off"""
        self.camera_active = not self.camera_active
        if self.camera_active:
            self.camera_button_text.set("Pause Camera")
            self.status_var.set("Camera active")
        else:
            self.camera_button_text.set("Resume Camera")
            self.status_var.set("Camera paused")
    
    def run_code(self):
        """Run the code from the editor"""
        code = self.code_editor.get("1.0", tk.END)
        self.execution_output = ""
        
        # Redirect stdout to capture output
        import sys
        from io import StringIO
        
        original_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            exec(code)
            self.execution_output = mystdout.getvalue()
            self.status_var.set("Code executed successfully")
        except Exception as e:
            self.execution_output = f"Error: {str(e)}"
            self.status_var.set(f"Error executing code: {str(e)}")
        finally:
            sys.stdout = original_stdout
            
        self.update_output_console()
    
    def clear_code(self):
        """Clear the code editor"""
        self.code_editor.delete("1.0", tk.END)
        self.generated_code = ""
        self.status_var.set("Code cleared")
    
    def save_code(self):
        """Save code to a file"""
        code = self.code_editor.get("1.0", tk.END)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"handycodes_{timestamp}.py"
        
        with open(filename, 'w') as f:
            f.write(code)
        
        self.status_var.set(f"Code saved to {filename}")
        self.update_output_console(f"Code saved to {filename}")
    
    def update_code_display(self):
        """Updates the code editor with newly generated code"""
        # Only update if there's a change
        current_code = self.code_editor.get("1.0", tk.END).strip()
        if current_code != self.generated_code.strip():
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert(tk.END, self.generated_code)
            self.code_editor.highlight()  # Apply syntax highlighting after inserting
            self.code_editor.update_line_numbers()  # Update line numbers
    
    def update_output_console(self, text=None):
        """Updates the output console with execution results"""
        self.output_console.config(state=tk.NORMAL)
        self.output_console.delete("1.0", tk.END)
        self.output_console.insert(tk.END, text if text else self.execution_output)
        self.output_console.config(state=tk.DISABLED)
        self.output_console.see(tk.END)  # Auto-scroll to the end
    
    def recognize_gesture(self, landmarks):
        """Detects hand gestures based on landmarks and returns corresponding gesture name"""
        try:
            # Simple defensive check - landmarks list must be long enough
            if len(landmarks) < 21:
                self.status_var.set("Warning: Incomplete hand landmarks detected")
                return None
            
            # Get specific landmark positions - with bounds checking
            thumb_tip = landmarks[4][1] if len(landmarks) > 4 else 0
            index_tip = landmarks[8][1] if len(landmarks) > 8 else 0
            middle_tip = landmarks[12][1] if len(landmarks) > 12 else 0
            ring_tip = landmarks[16][1] if len(landmarks) > 16 else 0
            pinky_tip = landmarks[20][1] if len(landmarks) > 20 else 0
            
            thumb_ip = landmarks[3][1] if len(landmarks) > 3 else 0
            thumb_mcp = landmarks[2][1] if len(landmarks) > 2 else 0
            index_pip = landmarks[6][1] if len(landmarks) > 6 else 0
            middle_pip = landmarks[10][1] if len(landmarks) > 10 else 0
            ring_pip = landmarks[14][1] if len(landmarks) > 14 else 0
            pinky_pip = landmarks[18][1] if len(landmarks) > 18 else 0
            
            # Calculate which fingers are extended
            try:
                thumb_extended = landmarks[4][0] > landmarks[3][0] if landmarks[4][0] > landmarks[2][0] else False
            except (IndexError, TypeError):
                thumb_extended = False
                
            try:
                index_extended = index_tip < index_pip
            except (IndexError, TypeError):
                index_extended = False
                
            try:
                middle_extended = middle_tip < middle_pip
            except (IndexError, TypeError):
                middle_extended = False
                
            try:
                ring_extended = ring_tip < ring_pip
            except (IndexError, TypeError):
                ring_extended = False
                
            try:
                pinky_extended = pinky_tip < pinky_pip
            except (IndexError, TypeError):
                pinky_extended = False
            
            extended_fingers = [thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]
            num_extended = sum(extended_fingers)

            # Classify gesture based on extended fingers
            if num_extended == 5:
                return "open_palm"
            elif num_extended == 0:
                return "fist"
            elif num_extended == 3:
                return "three_fingers"
            elif index_extended and not any([middle_extended, ring_extended, pinky_extended]):
                return "pointing_index"
            elif index_extended and middle_extended and not any([ring_extended, pinky_extended]):
                return "victory"
            elif thumb_extended and not any([index_extended, middle_extended, ring_extended, pinky_extended]):
                return "thumbs_up"
            else:
                return None
                
        except Exception as e:
            self.status_var.set(f"Error in gesture recognition: {str(e)}")
            return None
    
    def process_gesture(self, gesture):
        """Process recognized gesture and execute corresponding code"""
        try:
            current_time = time.time()
            
            if gesture != self.last_detected_gesture:
                self.gesture_start_time = time.time()
                self.last_detected_gesture = gesture
            elif time.time() - self.gesture_start_time >= self.gesture_hold_time:
                if current_time - self.last_executed_time > self.gesture_cooldown:
                    self.displayed_gesture = gesture
                    self.status_var.set(f"Recognized gesture: {gesture}")
                    
                    if gesture in self.gesture_code_mapping:
                        code_to_execute = self.gesture_code_mapping[gesture]
                        self.generated_code += code_to_execute + "\n"
                        self.update_code_display()
                        
                        # Execute code in output console
                        import sys
                        from io import StringIO
                        
                        original_stdout = sys.stdout
                        sys.stdout = mystdout = StringIO()
                        
                        try:
                            exec(code_to_execute)
                            output = mystdout.getvalue()
                        except Exception as e:
                            output = f"Error: {str(e)}"
                        finally:
                            sys.stdout = original_stdout
                        
                        # Append output to console
                        self.execution_output += f">>> {gesture}:\n{output}\n"
                        self.update_output_console()
                        
                        self.last_executed_time = current_time
        except Exception as e:
            self.status_var.set(f"Error processing gesture: {str(e)}")
    
    def start_camera(self):
        """Initialize the camera"""
        try:
            self.cap = cv2.VideoCapture(self.selected_camera)
            self.cap.set(3, 640)
            self.cap.set(4, 480)
            
            if not self.cap.isOpened():
                self.status_var.set(f"Failed to open camera {self.selected_camera}, trying default camera")
                self.selected_camera = 0
                self.cap = cv2.VideoCapture(self.selected_camera)
                if not self.cap.isOpened():
                    self.status_var.set("ERROR: Could not open any camera")
                    return False
            
            self.status_var.set(f"Camera {self.selected_camera} initialized")
            return True
        except Exception as e:
            self.status_var.set(f"Error starting camera: {str(e)}")
            return False
    
    def update_ui(self):
        """Update the UI (called periodically)"""
        try:
            self.root.update_idletasks()
            self.root.update()
            return self.running
        except Exception as e:
            self.status_var.set(f"UI update error: {str(e)}")
            return False
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()
    
    def run(self):
        """Run the application with integrated camera loop"""
        # Start camera
        if not self.start_camera():
            # If camera failed, still show UI
            self.root.mainloop()
            return
        
        self.running = True
        
        # Main loop that integrates camera and UI updates
        while self.running:
            try:
                # Process UI events
                if not self.update_ui():
                    break
                    
                # Skip camera processing if paused
                if not self.camera_active:
                    time.sleep(0.01)  # Small delay to prevent CPU hogging
                    continue
                    
                # Process camera frame
                ret, frame = self.cap.read()
                if not ret:
                    self.status_var.set("Camera error: Failed to grab frame")
                    time.sleep(0.1)
                    continue
                
                # Process the frame with MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                # Process hand landmarks if detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        try:
                            landmarks = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
                            gesture = self.recognize_gesture(landmarks)
                            
                            if gesture:
                                self.process_gesture(gesture)
                            
                            self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        except Exception as e:
                            self.status_var.set(f"Hand processing error: {str(e)}")
                
                # Display gesture info on the camera feed
                if self.displayed_gesture:
                    try:
                        height, width = frame.shape[:2]
                        y1, y2 = 40, 100  # Define region for the background
                        roi = frame[y1:y2, 0:width]
                        blurred_roi = cv2.GaussianBlur(roi, (81, 81), 0)
                        dark_tint = np.full(roi.shape, (30, 30, 30), dtype=np.uint8)
                        roi_dark = cv2.addWeighted(blurred_roi, 0.7, dark_tint, 0.3, 0)
                        frame[y1:y2, 0:width] = roi_dark
                        cv2.putText(frame, f"Gesture: {self.displayed_gesture}", (50, 80), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    except Exception as e:
                        self.status_var.set(f"Display overlay error: {str(e)}")
                
                # Show the camera window
                try:
                    cv2.imshow("HandyCodes Camera", frame)
                except Exception as e:
                    self.status_var.set(f"Camera display error: {str(e)}")
                
                # Check for key press to exit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                    break
                    
            except Exception as e:
                self.status_var.set(f"Main loop error: {str(e)}")
                time.sleep(0.5)  # Add delay to prevent error flooding
        
        # Clean up
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

# Run the application
if __name__ == "__main__":
    app = HandyCodesApp()
    app.run()