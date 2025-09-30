import tkinter as tk
import tkinter.ttk as ttk
import threading
import queue
from utils import is_image_file, is_video_file
from actions import convert_file, convert_to_mp4, compress_video, to_uppercase, to_lowercase, reverse_text, translate_text

# --------------------------------------------
# GUI POPUP
# --------------------------------------------

def start_conversion(file_list, func, root, progressbar, percent_label, cancel_event, btn_frame, bottom):
    """
    Run conversion in background thread and update UI safely via the main thread.
    - file_list: list[str]
    - func: conversion function that accepts (file_list, progress_callback, cancel_event?)
    - cancel_event: threading.Event to signal cancellation
    """
    if isinstance(file_list, str):
        file_list = [file_list]

    # Disable action buttons
    for child in btn_frame.winfo_children():
        try:
            child.config(state='disabled')
        except Exception:
            pass

    progressbar['value'] = 0
    progressbar.pack(fill='x', pady=(8, 0))
    percent_label.pack(in_=bottom, side='left')
    percent_label.config(text='0%')

    # Use a queue to receive progress updates from the worker
    q = queue.Queue()

    def progress_callback(p):
        # worker thread will call this
        q.put(p)

    def worker():
        try:
            # Some action functions may accept only (file_list, callback)
            try:
                func(file_list, progress_callback, cancel_event)
            except TypeError:
                func(file_list, progress_callback)
        except Exception:
            # Signal -1 for error
            q.put(-1)
        finally:
            q.put('done')

    threading.Thread(target=worker, daemon=True).start()

    def poll():
        try:
            while True:
                item = q.get_nowait()
                if item == 'done':
                    root.after(200, root.destroy)
                    return
                if item == -1:
                    percent_label.config(text='Error')
                    return
                # numeric progress
                try:
                    val = float(item)
                except Exception:
                    continue
                progressbar['value'] = max(0, min(100, val))
                percent_label.config(text=f"{int(progressbar['value'])}%")
        except queue.Empty:
            root.after(100, poll)

    root.after(100, poll)

def show_popup(x, y, context, data, hwnd):
    # Create a borderless root window that looks like a modern popup card
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"+{x}+{y}")

    # Use ttk styling for a modern look
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    container = ttk.Frame(root, padding=(12, 12, 12, 12), style='Card.TFrame')
    container.pack()

    header = ttk.Label(container, text="Actions", style='Header.TLabel')
    header.pack(anchor='w')

    btn_frame = ttk.Frame(container)
    btn_frame.pack(fill='x')

    # Progress widgets (hidden until used)
    progressbar = ttk.Progressbar(container, orient='horizontal', mode='determinate', maximum=100)
    percent_label = ttk.Label(container, text='')

    cancel_event = threading.Event()

    # Helper to run a quick action and then close the popup after a short delay
    def run_and_close(fn, *args, delay=200):
        try:
            fn(*args)
        except Exception as e:
            print(f"Action error: {e}")
        # schedule close shortly after to allow clipboard/paste to happen
        root.after(delay, root.destroy)

    def add_action_button(text, command):
        b = ttk.Button(btn_frame, text=text, command=command)
        b.pack(fill='x', pady=4)
        return b

    if context == 'text':
        add_action_button('To Uppercase', lambda: run_and_close(to_uppercase, data, hwnd))
        add_action_button('To Lowercase', lambda: run_and_close(to_lowercase, data, hwnd))
        add_action_button('Reverse', lambda: run_and_close(reverse_text, data, hwnd))
        add_action_button('Translate', lambda: run_and_close(translate_text, data, hwnd))

    elif context == 'file':
        image_files = [f for f in data if is_image_file(f)]
        video_files = [f for f in data if is_video_file(f)]

        if image_files:
            add_action_button(f"Convert {len(image_files)} Image(s)",
                              lambda: start_conversion(image_files, convert_file, root, progressbar, percent_label, cancel_event, btn_frame, bottom))

        if video_files:
            non_mp4 = [f for f in video_files if not f.lower().endswith('.mp4')]
            if non_mp4:
                add_action_button(f"Convert {len(non_mp4)} to MP4",
                                  lambda: start_conversion(non_mp4, convert_to_mp4, root, progressbar, percent_label, cancel_event, btn_frame, bottom))
            add_action_button(f"Compress {len(video_files)} Video(s)",
                              lambda: start_conversion(video_files, compress_video, root, progressbar, percent_label, cancel_event, btn_frame, bottom))

    else:
        ttk.Label(btn_frame, text="No actions available").pack()

    # Bottom row: percent label and cancel/close button
    bottom = ttk.Frame(container)
    bottom.pack(fill='x', pady=(8, 0))

    def on_cancel():
        cancel_event.set()
        root.destroy()

    ttk.Button(bottom, text='Cancel', command=on_cancel).pack(side='right')

    # Place progressbar just above bottom and hide until needed
    progressbar.pack_forget()
    percent_label.config(text='')

    # Close on ESC
    root.bind('<Escape>', lambda e: root.destroy())

    # Close on focus out only when focus truly leaves the popup (not when clicking child widgets)
    def on_focus_out(event):
        # Determine which widget currently has focus
        focused = root.focus_get()
        if not focused:
            root.destroy()
            return
        # Walk up the master chain to see if focus is inside this root
        w = focused
        while w:
            if w == root:
                return  # focus still within popup
            w = getattr(w, 'master', None)
        # focus is outside the popup
        root.destroy()

    root.focus_force()
    root.mainloop()
