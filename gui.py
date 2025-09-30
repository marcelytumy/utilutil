import tkinter as tk
import tkinter.ttk as ttk
import threading
from utils import is_image_file, is_video_file
from actions import convert_file, convert_to_mp4, compress_video, to_uppercase, to_lowercase, reverse_text, translate_text

# --------------------------------------------
# GUI POPUP
# --------------------------------------------

def start_conversion(file_list, func, root, progress, frame):
    if isinstance(file_list, str):
        file_list = [file_list]
    # Disable all buttons
    for child in frame.winfo_children():
        if isinstance(child, tk.Button):
            child.config(state='disabled')
    progress.pack()  # Show progress
    progress.config(mode='determinate', maximum=100, value=0)

    def progress_callback(p):
        progress.config(value=p)
        root.update_idletasks()

    func(file_list, progress_callback)
    progress.pack_forget()
    root.destroy()

def show_popup(x, y, context, data, hwnd):
    root = tk.Tk()
    root.overrideredirect(True)  # Removes window decorations
    root.attributes("-topmost", True)
    root.geometry(f"+{x}+{y}")
    root.configure(bg='white')

    frame = tk.Frame(root, bg='white', padx=10, pady=10)
    frame.pack()

    progress = ttk.Progressbar(frame, mode='indeterminate')
    progress.pack(pady=5)
    progress.pack_forget()  # Hide initially

    if context == 'text':
        label = tk.Label(frame, text=f"Text: {data[:40]}...", bg='white')
        label.pack()
        buttons = [
            ("To Uppercase", lambda: [to_uppercase(data, hwnd), root.destroy()]),
            ("To Lowercase", lambda: [to_lowercase(data, hwnd), root.destroy()]),
            ("Reverse", lambda: [reverse_text(data, hwnd), root.destroy()]),
            ("Translate", lambda: [translate_text(data, hwnd), root.destroy()]),
        ]
        for text_btn, cmd in buttons:
            btn = tk.Button(frame, text=text_btn, command=cmd)
            btn.pack(pady=5)

    elif context == 'file':
        image_files = [f for f in data if is_image_file(f)]
        video_files = [f for f in data if is_video_file(f)]

        if image_files:
            btn = tk.Button(frame, text=f"Convert {len(image_files)} Image(s)",
                            command=lambda: start_conversion(image_files, convert_file, root, progress, frame))
            btn.pack(pady=5)

        if video_files:
            non_mp4 = [f for f in video_files if not f.lower().endswith('.mp4')]
            if non_mp4:
                btn = tk.Button(frame, text=f"Convert {len(non_mp4)} to MP4",
                                command=lambda: start_conversion(non_mp4, convert_to_mp4, root, progress, frame))
                btn.pack(pady=5)
            btn = tk.Button(frame, text=f"Compress {len(video_files)} Video(s)",
                            command=lambda: start_conversion(video_files, compress_video, root, progress, frame))
            btn.pack(pady=5)

        # Skip other file types

    else:
        label = tk.Label(frame, text="No valid context detected.", bg='white')
        label.pack()

    # Bind ESC to close
    root.bind('<Escape>', lambda e: root.destroy())
    # Bind focus out to close (click away)
    root.bind('<FocusOut>', lambda e: root.destroy())

    root.focus_force()  # Ensure the popup is focused
    root.mainloop()