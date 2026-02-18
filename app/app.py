#!/usr/bin/env python3
"""
Image Resizer App
Batch resize images to a specified size on the longest side while maintaining aspect ratio.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from pathlib import Path


class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Resizer")
        self.root.geometry("600x400")
        
        # Default size
        self.target_size = 1024
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Batch Image Resizer", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Size selection frame
        size_frame = tk.Frame(self.root)
        size_frame.pack(pady=10)
        
        tk.Label(size_frame, text="Target size (longest side):").pack(side=tk.LEFT, padx=5)
        
        self.size_var = tk.StringVar(value="1024")
        size_combo = ttk.Combobox(size_frame, textvariable=self.size_var, 
                                   values=["512", "768", "1024"],
                                   state="readonly", width=10)
        size_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(size_frame, text="pixels").pack(side=tk.LEFT, padx=5)
        
        # Select files button
        select_btn = tk.Button(self.root, text="Select Images", 
                              command=self.select_images,
                              bg="#4CAF50", fg="white",
                              font=("Arial", 12),
                              padx=20, pady=10)
        select_btn.pack(pady=20)
        
        # Status frame
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Status text with scrollbar
        scroll = tk.Scrollbar(status_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_text = tk.Text(status_frame, height=10, width=60, 
                                   yscrollcommand=scroll.set, state=tk.DISABLED)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.status_text.yview)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(pady=10, padx=20, fill=tk.X)
        
    def log_status(self, message):
        """Add a message to the status text area"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
        
    def select_images(self):
        """Open file dialog and process selected images"""
        # Validate size input
        try:
            self.target_size = int(self.size_var.get())
            if self.target_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive number for size.")
            return
        
        # Open file dialog
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
            ("All files", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="Select images to resize",
            filetypes=filetypes
        )
        
        if not file_paths:
            return
        
        # Ask for output folder
        output_folder = filedialog.askdirectory(
            title="Select output folder for resized images"
        )
        
        if not output_folder:
            return
        
        # Clear previous status
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Process images
        self.process_images(file_paths, output_folder)
        
    def resize_image(self, input_path, output_path, target_size):
        """Resize a single image"""
        try:
            # Open image
            img = Image.open(input_path)
            
            # Get original dimensions
            width, height = img.size
            
            # Calculate new dimensions
            if width > height:
                new_width = target_size
                new_height = int(height * (target_size / width))
            else:
                new_height = target_size
                new_width = int(width * (target_size / height))
            
            # Resize image with high-quality resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with original format or fallback to PNG
            try:
                resized_img.save(output_path, quality=95, optimize=True)
            except:
                # If format not supported for saving, convert to PNG
                output_path = os.path.splitext(output_path)[0] + '.png'
                resized_img.save(output_path, 'PNG', quality=95, optimize=True)
            
            return True, f"{width}x{height} → {new_width}x{new_height}"
            
        except Exception as e:
            return False, str(e)
    
    def process_images(self, file_paths, output_folder):
        """Process multiple images"""
        total = len(file_paths)
        success_count = 0
        
        self.progress['maximum'] = total
        self.progress['value'] = 0
        
        self.log_status(f"Processing {total} image(s)...")
        self.log_status(f"Target size: {self.target_size}px on longest side")
        self.log_status(f"Output folder: {output_folder}\n")
        
        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            # Create output filename
            output_filename = f"{name}_resized{ext}"
            output_path = os.path.join(output_folder, output_filename)
            
            # Resize image
            success, info = self.resize_image(file_path, output_path, self.target_size)
            
            if success:
                self.log_status(f"✓ {filename}: {info}")
                success_count += 1
            else:
                self.log_status(f"✗ {filename}: ERROR - {info}")
            
            # Update progress
            self.progress['value'] = i
            self.root.update()
        
        # Show summary
        self.log_status(f"\nCompleted! {success_count}/{total} images resized successfully.")
        
        if success_count > 0:
            messagebox.showinfo("Success", 
                              f"Resized {success_count} out of {total} image(s)!\n\n"
                              f"Saved to: {output_folder}")


def main():
    root = tk.Tk()
    app = ImageResizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

