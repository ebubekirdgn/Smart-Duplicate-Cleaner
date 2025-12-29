import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

duplicates_global = {}

# Dosya hash hesaplama
def calculate_hash(file_path, chunk_size=8192):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

# Kopya dosyaları bul
def find_duplicate_files(folder_path, output_box):
    global duplicates_global
    hashes = {}
    duplicates = {}

    output_box.insert(tk.END, "Scan started...\n\n")
    output_box.update()

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = calculate_hash(file_path)

            if not file_hash:
                continue

            if file_hash in hashes:
                duplicates.setdefault(file_hash, [hashes[file_hash]])
                duplicates[file_hash].append(file_path)
            else:
                hashes[file_hash] = file_path

    duplicates_global = duplicates

    if not duplicates:
        output_box.insert(tk.END, "No duplicate files found.\n")
        return

    for i, (file_hash, files) in enumerate(duplicates.items(), start=1):
        output_box.insert(
            tk.END,
            f"\nDUPLICATE SET {i} (Total {len(files)} files)\nHash: {file_hash}\n"
        )
        for f in files:
            output_box.insert(tk.END, f"  {f}\n")

# Kopyaları sil
def delete_duplicates(output_box):
    global duplicates_global

    if not duplicates_global:
        messagebox.showwarning("Warning", "No duplicates found to delete.")
        return

    confirm = messagebox.askyesno(
        "Confirm",
        "One file will be kept from each duplicate group.\nAll other duplicates will be permanently deleted.\nDo you want to continue?"
    )

    if not confirm:
        return

    output_box.insert(tk.END, "\n--- DELETE OPERATION STARTED ---\n")

    deleted_count = 0

    for file_hash, files in duplicates_global.items():
        # İlk dosya kalsın, diğerleri silinsin
        for file_to_delete in files[1:]:
            try:
                os.remove(file_to_delete)
                output_box.insert(tk.END, f"DELETED: {file_to_delete}\n")
                deleted_count += 1
            except Exception as e:
                output_box.insert(
                    tk.END,
                    f"COULD NOT DELETE: {file_to_delete} | Error: {e}\n"
                )

    output_box.insert(
        tk.END,
        f"\n--- DELETE COMPLETED | Total deleted files: {deleted_count} ---\n"
    )

    duplicates_global = {}

# Klasör seç
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

# Başlat
def start_scan():
    folder = folder_var.get()
    if not folder:
        messagebox.showwarning("Warning", "Please select a folder first.")
        return

    output_box.delete(1.0, tk.END)
    find_duplicate_files(folder, output_box)

# --- TKINTER ARAYÜZ ---
root = tk.Tk()
root.title("Duplicate File Finder & Remover (Hash-based)")
root.geometry("950x650")

folder_var = tk.StringVar()

frame_top = tk.Frame(root)
frame_top.pack(pady=10)

btn_select = tk.Button(frame_top, text="Open Folder", command=select_folder, width=20)
btn_select.pack(side=tk.LEFT, padx=5)

entry_folder = tk.Entry(frame_top, textvariable=folder_var, width=85)
entry_folder.pack(side=tk.LEFT, padx=5)

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

btn_start = tk.Button(
    frame_buttons,
    text="Start",
    command=start_scan,
    width=20,
    bg="#4CAF50",
    fg="white"
)
btn_start.pack(side=tk.LEFT, padx=10)

btn_delete = tk.Button(
    frame_buttons,
    text="Delete Duplicates",
    command=lambda: delete_duplicates(output_box),
    width=20,
    bg="#E53935",
    fg="white"
)
btn_delete.pack(side=tk.LEFT, padx=10)

output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=30)
output_box.pack(padx=10, pady=10)

root.mainloop()
