import os
import hashlib
import threading
import queue
import concurrent.futures
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import csv


class DuplicateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Duplicate Cleaner Pro")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self.scan_executor = None
        self.stop_event = threading.Event()
        self.duplicates = {}
        self.file_queue = queue.Queue()
        self.scanned_count = 0
        self.total_files = 0
        self.hash_workers = 4
        self.chunk_size = 65536
        self.current_group_id = 0
        self.group_items = {}
        self.group_keep_paths = {}

        self._setup_styles()
        self._build_ui()
        self._load_settings()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#0078d7")], foreground=[("selected", "white")])
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Accent.TButton", background="#0078d7", foreground="white")
        style.configure("Danger.TButton", background="#d13438", foreground="white")
        style.configure("Secondary.TButton", background="#e1e1e1", foreground="#333")
        style.configure("Group.TLabel", font=("Segoe UI", 10, "bold"), foreground="#0078d7")
        style.configure("File.TLabel", font=("Segoe UI", 10), foreground="#333")
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#666")
        style.configure("TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top bar - Folder selection
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(top_frame, text="📁 Klasör Seç", command=self._select_folder, width=18).pack(side=tk.LEFT, padx=(0, 8))
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, width=70, font=("Segoe UI", 10))
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.btn_start = ttk.Button(btn_frame, text="▶ Taramayı Başlat", command=self._start_scan, style="Accent.TButton", width=22)
        self.btn_start.pack(side=tk.LEFT, padx=4)

        self.btn_stop = ttk.Button(btn_frame, text="⏹ Durdur", command=self._stop_scan, width=16, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_delete = ttk.Button(btn_frame, text="🗑 Kopyaları Sil", command=self._delete_selected, style="Danger.TButton", width=20, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_frame, text="☑ Her Grupta İlkini Tut", command=self._keep_first_in_groups, width=22).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="📤 Dışa Aktar", command=self._export_results, width=16).pack(side=tk.LEFT, padx=4)

        # Auto-select frame
        auto_frame = ttk.LabelFrame(main_frame, text="Otomatik Seçim", padding=8)
        auto_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(auto_frame, text="📅 En Eskiyi Tut", command=lambda: self._auto_select("oldest"), width=16).pack(side=tk.LEFT, padx=4)
        ttk.Button(auto_frame, text="📅 En Yeniyi Tut", command=lambda: self._auto_select("newest"), width=16).pack(side=tk.LEFT, padx=4)
        ttk.Button(auto_frame, text="📏 En Kısa Yolu Tut", command=lambda: self._auto_select("shortest"), width=18).pack(side=tk.LEFT, padx=4)
        ttk.Button(auto_frame, text="📂 Aynı Klasörde Tut", command=lambda: self._auto_select("same_folder"), width=18).pack(side=tk.LEFT, padx=4)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 8))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, mode="determinate")
        self.progress_bar.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Hazır")
        ttk.Label(progress_frame, textvariable=self.status_var, style="Status.TLabel").pack(anchor=tk.W, pady=(4, 0))

        # Results - Paned window for tree + preview
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left: Tree view
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)

        columns = ("keep", "name", "path", "size", "modified")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="Gruplar")
        self.tree.heading("keep", text="Tut")
        self.tree.heading("name", text="Dosya Adı")
        self.tree.heading("path", text="Yol")
        self.tree.heading("size", text="Boyut")
        self.tree.heading("modified", text="Değiştirilme")

        self.tree.column("#0", width=300, minwidth=200, stretch=True)
        self.tree.column("keep", width=40, anchor=tk.CENTER, stretch=False)
        self.tree.column("name", width=200, anchor=tk.W, minwidth=150)
        self.tree.column("path", width=350, anchor=tk.W, minwidth=200)
        self.tree.column("size", width=100, anchor=tk.E, stretch=False)
        self.tree.column("modified", width=150, anchor=tk.CENTER, stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<space>", self._toggle_keep)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_group_expand)
        self.tree.bind("<<TreeviewClose>>", self._on_group_collapse)

        # Right: Preview panel
        preview_frame = ttk.LabelFrame(paned, text="Önizleme", padding=8)
        paned.add(preview_frame, weight=1)

        self.preview_label = ttk.Label(preview_frame, text="Dosya seçiniz", style="Status.TLabel", anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.preview_canvas = tk.Canvas(preview_frame, bg="#f5f5f5", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, font=("Consolas", 9), state=tk.DISABLED, bg="#fafafa")
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Stats
        self.stats_var = tk.StringVar(value="Dosya: 0 | Kopya Grupları: 0 | Toplam Kopya: 0 | Boşluk: 0 B")
        ttk.Label(main_frame, textvariable=self.stats_var, font=("Segoe UI", 9), foreground="#444").pack(anchor=tk.W, pady=(8, 0))

        # Context menu
        self._create_context_menu()

    def _create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        self.context_menu.add_command(label="📂 Konumu Aç", command=self._open_file_location)
        self.context_menu.add_command(label="📄 Özellikler", command=self._show_properties)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="☑ Bu Dosyayı Tut", command=lambda: self._toggle_context_item(True))
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _toggle_context_item(self, check):
        for item in self.tree.selection():
            self._set_item_check(item, check)

    def _load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                hash_workers = settings.get("hash_workers", 4)
                chunk_size = settings.get("chunk_size", 65536)
                if isinstance(hash_workers, int) and not isinstance(hash_workers, bool) and 1 <= hash_workers <= 32:
                    self.hash_workers = hash_workers
                if isinstance(chunk_size, int) and not isinstance(chunk_size, bool) and 4096 <= chunk_size <= 16 * 1024 * 1024:
                    self.chunk_size = chunk_size
                last_folder = settings.get("last_folder", "")
                if last_folder and os.path.isdir(last_folder):
                    self.folder_var.set(last_folder)
        except Exception:
            pass

    def _save_settings(self):
        try:
            settings = {
                "hash_workers": self.hash_workers,
                "chunk_size": self.chunk_size,
                "last_folder": self.folder_var.get()
            }
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass

    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self._save_settings()

    def _start_scan(self):
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Uyarı", "Geçerli bir klasör seçin.")
            return

        self._reset_ui()
        self.stop_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.DISABLED)

        self.scan_thread = threading.Thread(target=self._scan_worker, args=(folder,), daemon=True)
        self.scan_thread.start()
        self.root.after(100, self._process_queue)

    def _stop_scan(self):
        self.stop_event.set()
        self.status_var.set("Durduruluyor...")
        self.btn_stop.config(state=tk.DISABLED)

    def _reset_ui(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.duplicates.clear()
        self.group_items.clear()
        self.group_keep_paths.clear()
        self.current_group_id = 0
        self.scanned_count = 0
        self.total_files = 0
        self.progress_var.set(0)
        self.status_var.set("Taranıyor...")
        self.stats_var.set("Dosya: 0 | Kopya Grupları: 0 | Toplam Kopya: 0 | Boşluk: 0 B")
        self._clear_preview()

    def _scan_worker(self, folder):
        terminal_message = None
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.hash_workers)
        self.scan_executor = executor
        try:
            # First pass: collect files by size (fast, single-threaded)
            size_map = {}
            file_count = 0
            for root, _, files in os.walk(folder):
                if self.stop_event.is_set():
                    self.file_queue.put(("stopped", None))
                    return
                for f in files:
                    path = os.path.join(root, f)
                    try:
                        size = os.path.getsize(path)
                        if size == 0:
                            continue
                        size_map.setdefault(size, []).append(path)
                        file_count += 1
                    except OSError:
                        continue

            self.total_files = sum(len(paths) for paths in size_map.values() if len(paths) > 1)
            self.file_queue.put(("total", self.total_files, file_count))

            # A small first/last-block hash eliminates most candidates before
            # their full contents need to be read.
            hashes = {}
            completed = 0
            last_reported = 0
            progress_step = max(1, self.total_files // 100)

            def report_progress(increment):
                nonlocal completed, last_reported
                completed += increment
                if completed - last_reported >= progress_step or completed == self.total_files:
                    last_reported = completed
                    self.scanned_count = completed
                    self.file_queue.put(("progress", completed))

            for size, paths in size_map.items():
                if len(paths) < 2:
                    continue
                if self.stop_event.is_set():
                    terminal_message = ("stopped", None)
                    return

                sample_groups = {}
                failed_samples = 0
                for path, sample_hash in self._bounded_hash(executor, paths, self._calculate_sample_hash):
                    if sample_hash:
                        sample_groups.setdefault(sample_hash, []).append(path)
                    else:
                        failed_samples += 1
                if self.stop_event.is_set():
                    terminal_message = ("stopped", None)
                    return
                report_progress(failed_samples)

                full_hash_paths = []
                for sample_paths in sample_groups.values():
                    if len(sample_paths) > 1:
                        full_hash_paths.extend(sample_paths)
                    else:
                        report_progress(1)

                for path, file_hash in self._bounded_hash(executor, full_hash_paths, self._calculate_hash):
                    if file_hash:
                        hashes.setdefault((size, file_hash), []).append(path)
                    report_progress(1)
                if self.stop_event.is_set():
                    terminal_message = ("stopped", None)
                    return

            # Collect duplicates
            self.duplicates = {k: v for k, v in hashes.items() if len(v) > 1}
            terminal_message = ("done", len(self.duplicates))

        except Exception as e:
            terminal_message = ("error", str(e))
        finally:
            executor.shutdown(wait=True)
            if self.scan_executor is executor:
                self.scan_executor = None
            if terminal_message:
                self.file_queue.put(terminal_message)

    def _bounded_hash(self, executor, paths, hash_function):
        paths = iter(paths)
        futures = {}
        max_pending = max(self.hash_workers, self.hash_workers * 4)

        def submit_next():
            if self.stop_event.is_set():
                return False
            try:
                path = next(paths)
            except StopIteration:
                return False
            futures[executor.submit(hash_function, path)] = path
            return True

        for _ in range(max_pending):
            if not submit_next():
                break

        while futures:
            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                path = futures.pop(future)
                try:
                    result = future.result()
                except Exception:
                    result = None
                yield path, result
                submit_next()

    def _calculate_sample_hash(self, filepath, sample_size=65536):
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                initial = os.fstat(f.fileno())
                sha256.update(f.read(sample_size))
                if initial.st_size > sample_size:
                    f.seek(max(sample_size, initial.st_size - sample_size))
                    sha256.update(f.read(sample_size))
                final = os.fstat(f.fileno())
            if initial.st_size != final.st_size or initial.st_mtime_ns != final.st_mtime_ns:
                return None
            return sha256.hexdigest()
        except (OSError, ValueError):
            return None

    def _calculate_hash(self, filepath, chunk_size=None):
        if chunk_size is None:
            chunk_size = self.chunk_size
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                initial = os.fstat(f.fileno())
                while chunk := f.read(chunk_size):
                    if self.stop_event.is_set():
                        return None
                    sha256.update(chunk)
                final = os.fstat(f.fileno())
            if initial.st_size != final.st_size or initial.st_mtime_ns != final.st_mtime_ns:
                return None
            return sha256.hexdigest()
        except (OSError, ValueError):
            return None

    def _process_queue(self):
        try:
            while True:
                msg = self.file_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "total":
                    self.total_files = msg[1]
                    self.progress_bar.config(maximum=msg[1])
                    self.status_var.set(f"Bulunan dosya: {msg[2]} | Taranacak: {msg[1]}")
                elif msg_type == "progress":
                    self.scanned_count = msg[1]
                    self.progress_var.set(msg[1])
                    pct = (msg[1] / self.total_files * 100) if self.total_files else 0
                    self.status_var.set(f"Taranıyor: {msg[1]}/{self.total_files} ({pct:.1f}%)")
                elif msg_type == "done":
                    self._populate_tree(msg[1])
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_stop.config(state=tk.DISABLED)
                    if msg[1] > 0:
                        self.btn_delete.config(state=tk.NORMAL)
                    return
                elif msg_type == "stopped":
                    self.status_var.set("Durduruldu")
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_stop.config(state=tk.DISABLED)
                    return
                elif msg_type == "error":
                    messagebox.showerror("Hata", f"Tarama hatası: {msg[1]}")
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_stop.config(state=tk.DISABLED)
                    return
        except queue.Empty:
            pass

        if self.scan_thread and self.scan_thread.is_alive():
            self.root.after(100, self._process_queue)

    def _populate_tree(self, group_count):
        total_dupes = 0
        total_wasted = 0

        # Sort groups by wasted space (descending)
        sorted_groups = sorted(
            self.duplicates.items(),
            key=lambda x: (len(x[1]) - 1) * x[0][0],
            reverse=True
        )

        for (size, fhash), paths in sorted_groups:
            if self.stop_event.is_set():
                break

            group_size = size
            wasted = group_size * (len(paths) - 1)
            total_wasted += wasted
            total_dupes += len(paths) - 1

            group_id = f"group_{self.current_group_id}"
            self.current_group_id += 1

            # Group header
            group_text = f"{len(paths)} dosya · {self._format_size(group_size)} each · Boşluk: {self._format_size(wasted)}"
            group_item = self.tree.insert("", tk.END, iid=group_id, text=group_text, open=False, tags=("group",))
            self.group_items[group_id] = paths
            self.group_keep_paths[group_id] = paths[0]

            # Files in group (lazy loaded on expand)
            self.tree.insert(group_id, tk.END, iid=f"{group_id}_placeholder", text="Yükleniyor...")

        self.stats_var.set(f"Dosya: {self.scanned_count} | Kopya Grupları: {group_count} | Toplam Kopya: {total_dupes} | Boşluk: {self._format_size(total_wasted)}")
        self.status_var.set(f"Tamamlandı - {group_count} kopya grubu bulundu")

    def _on_group_expand(self, event):
        item = self.tree.focus()
        if self._is_group_item(item):
            children = self.tree.get_children(item)
            if len(children) == 1 and children[0].endswith("_placeholder"):
                self.tree.delete(children[0])
                self._load_group_files(item)

    def _load_group_files(self, group_id):
        paths = self.group_items.get(group_id, [])
        keep_path = self.group_keep_paths.get(group_id)
        for i, path in enumerate(paths):
            try:
                stat = os.stat(path)
                size_str = self._format_size(stat.st_size)
                mod_str = self._format_time(stat.st_mtime)
                name = os.path.basename(path)
                keep = "☑" if path == keep_path else "☐"
                file_id = f"{group_id}_file_{i}"
                self.tree.insert(group_id, tk.END, iid=file_id, text="", values=(keep, name, path, size_str, mod_str), tags=("file",))
            except OSError:
                continue

    def _on_group_collapse(self, event):
        pass

    def _format_size(self, bytes_):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_ < 1024:
                return f"{bytes_:.1f} {unit}"
            bytes_ /= 1024
        return f"{bytes_:.1f} PB"

    def _format_time(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                item = self.tree.identify_row(event.y)
                if self._is_file_item(item):
                    self._toggle_keep_item(item)
        elif region == "tree":
            item = self.tree.identify_row(event.y)
            if self._is_group_item(item):
                self._show_group_preview(item)

    def _toggle_keep(self, event):
        item = self.tree.focus()
        if self._is_file_item(item):
            self._toggle_keep_item(item)

    def _toggle_keep_item(self, item):
        vals = self.tree.item(item, "values")
        if vals:
            self._set_group_keep(self.tree.parent(item), vals[2])
            self._show_file_preview(item)

    def _set_item_check(self, item, check):
        if self._is_file_item(item) and check:
            vals = self.tree.item(item, "values")
            if vals:
                self._set_group_keep(self.tree.parent(item), vals[2])

    def _is_group_item(self, item):
        return bool(item) and "group" in self.tree.item(item, "tags")

    def _is_file_item(self, item):
        return bool(item) and "file" in self.tree.item(item, "tags")

    def _set_group_keep(self, group_id, keep_path):
        if keep_path not in self.group_items.get(group_id, []):
            return
        self.group_keep_paths[group_id] = keep_path
        for child in self.tree.get_children(group_id):
            if not self._is_file_item(child):
                continue
            vals = list(self.tree.item(child, "values"))
            vals[0] = "☑" if vals[2] == keep_path else "☐"
            self.tree.item(child, values=vals)

    def _keep_first_in_groups(self):
        for group_id, paths in self.group_items.items():
            if paths:
                self._set_group_keep(group_id, paths[0])

    def _auto_select(self, mode):
        for group_id, paths in self.group_items.items():
            files_info = []
            for path in paths:
                try:
                    stat = os.stat(path)
                    files_info.append({
                        "path": path,
                        "mtime": stat.st_mtime,
                        "path_len": len(path)
                    })
                except OSError:
                    continue

            if not files_info:
                continue

            if mode == "oldest":
                keep_path = min(files_info, key=lambda x: x["mtime"])["path"]
            elif mode == "newest":
                keep_path = max(files_info, key=lambda x: x["mtime"])["path"]
            elif mode == "shortest":
                keep_path = min(files_info, key=lambda x: x["path_len"])["path"]
            elif mode == "same_folder":
                group_path = os.path.dirname(files_info[0]["path"])
                same_folder = [f for f in files_info if os.path.dirname(f["path"]) == group_path]
                keep_path = same_folder[0]["path"] if same_folder else files_info[0]["path"]
            else:
                keep_path = files_info[0]["path"]

            self._set_group_keep(group_id, keep_path)

    def _on_double_click(self, event):
        item = self.tree.focus()
        if self._is_file_item(item):
            self._open_file_location()

    def _show_file_preview(self, item):
        vals = self.tree.item(item, "values")
        if not vals:
            return
        path = vals[2]
        self._load_preview(path)

    def _show_group_preview(self, group_id):
        paths = self.group_items.get(group_id, [])
        if paths:
            self._load_preview(paths[0])

    def _load_preview(self, path):
        self._clear_preview()
        self.preview_label.config(text=os.path.basename(path))

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'):
                self._preview_image(path)
            elif ext in ('.txt', '.log', '.md', '.py', '.js', '.json', '.xml', '.csv', '.ini', '.cfg'):
                self._preview_text(path)
            else:
                self.preview_label.config(text=f"{os.path.basename(path)}\n({self._format_size(os.path.getsize(path))}) - Önizleme desteklenmiyor")
        except Exception as e:
            self.preview_label.config(text=f"Önizleme hatası: {e}")

    def _preview_image(self, path):
        self.preview_text.pack_forget()
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            canvas_w = self.preview_canvas.winfo_width() or 300
            canvas_h = self.preview_canvas.winfo_height() or 300
            img.thumbnail((canvas_w - 20, canvas_h - 20), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(canvas_w // 2, canvas_h // 2, image=photo, anchor=tk.CENTER)
            self.preview_canvas.image = photo
        except Exception:
            self.preview_canvas.pack_forget()
            self.preview_text.pack(fill=tk.BOTH, expand=True)
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Görsel yüklenemedi: {path}")
            self.preview_text.config(state=tk.DISABLED)

    def _preview_text(self, path):
        self.preview_canvas.pack_forget()
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(5000)
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, content)
            if len(content) >= 5000:
                self.preview_text.insert(tk.END, "\n\n... (kesildi)")
            self.preview_text.config(state=tk.DISABLED)
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Metin yüklenemedi: {e}")
            self.preview_text.config(state=tk.DISABLED)

    def _clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.image = None
        self.preview_canvas.pack_forget()
        self.preview_text.pack_forget()
        self.preview_label.config(text="Dosya seçiniz")

    def _open_file_location(self):
        item = self.tree.focus()
        if not self._is_file_item(item):
            return
        vals = self.tree.item(item, "values")
        if not vals:
            return
        path = vals[2]
        folder = os.path.dirname(path)
        try:
            if os.name == 'nt':
                os.startfile(folder)
            else:
                import subprocess
                subprocess.run(['xdg-open', folder])
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı: {e}")

    def _show_properties(self):
        item = self.tree.focus()
        if not self._is_file_item(item):
            return
        vals = self.tree.item(item, "values")
        if not vals:
            return
        path = vals[2]
        try:
            stat = os.stat(path)
            info = f"Dosya: {os.path.basename(path)}\n"
            info += f"Yol: {path}\n"
            info += f"Boyut: {self._format_size(stat.st_size)} ({stat.st_size} bayt)\n"
            info += f"Oluşturulma: {self._format_time(stat.st_ctime)}\n"
            info += f"Değiştirilme: {self._format_time(stat.st_mtime)}\n"
            info += f"Erişim: {self._format_time(stat.st_atime)}"
            messagebox.showinfo("Dosya Özellikleri", info)
        except Exception as e:
            messagebox.showerror("Hata", f"Özellikler alınamadı: {e}")

    def _delete_selected(self):
        delete_plan = []
        for group_id, paths in self.group_items.items():
            if len(paths) < 2:
                continue
            keep_path = self.group_keep_paths.get(group_id)
            if keep_path not in paths:
                keep_path = paths[0]
                self.group_keep_paths[group_id] = keep_path
            delete_plan.append((group_id, keep_path, [path for path in paths if path != keep_path]))

        delete_count = sum(len(paths) for _, _, paths in delete_plan)
        if not delete_count:
            messagebox.showinfo("Bilgi", "Silinecek kopya bulunamadı.")
            return

        confirm = messagebox.askyesno(
            "Onay",
            f"{len(delete_plan)} gruptaki {delete_count} kopya kalıcı olarak silinecek.\n"
            "Her grupta Tut sütununda işaretli bir dosya korunacak.\n"
            "Bu işlem GERİ ALINAMAZ. Devam etmek istiyor musunuz?",
            icon="warning"
        )
        if not confirm:
            return

        deleted = 0
        errors = []
        changed = []
        for group_id, keep_path, targets in delete_plan:
            if not os.path.isfile(keep_path):
                errors.append(f"Korunacak dosya bulunamadı: {keep_path}")
                continue

            remaining_paths = [keep_path]
            for path in targets:
                if not os.path.lexists(path):
                    self._remove_path_from_tree(group_id, path)
                    continue
                try:
                    if not self._files_equal(keep_path, path):
                        changed.append(path)
                        self._remove_path_from_tree(group_id, path)
                        continue
                    os.remove(path)
                    deleted += 1
                    self._remove_path_from_tree(group_id, path)
                except OSError as e:
                    remaining_paths.append(path)
                    errors.append(f"{path}: {e}")

            if len(remaining_paths) == 1:
                if self.tree.exists(group_id):
                    self.tree.delete(group_id)
                self.group_items.pop(group_id, None)
                self.group_keep_paths.pop(group_id, None)
            else:
                self.group_items[group_id] = remaining_paths
                self._update_group_header(group_id, remaining_paths)

        self.btn_delete.config(state=tk.NORMAL if self.group_items else tk.DISABLED)
        message = f"Silinen kopya: {deleted}\nKalan kopya grubu: {len(self.group_items)}"
        if errors:
            details = "\n".join(errors[:10])
            if len(errors) > 10:
                details += f"\n... ve {len(errors) - 10} hata daha"
            if changed:
                details += f"\n{len(changed)} dosya taramadan sonra değiştiği için silinmedi."
            messagebox.showwarning("Kısmen Tamamlandı", f"{message}\n\n{details}")
        elif changed:
            messagebox.showwarning(
                "Tamamlandı",
                f"{message}\n\n{len(changed)} dosya taramadan sonra değiştiği için silinmedi."
            )
        else:
            messagebox.showinfo("Tamam", message)
        self._update_stats_after_delete()

    def _files_equal(self, first_path, second_path):
        if os.path.getsize(first_path) != os.path.getsize(second_path):
            return False
        with open(first_path, "rb") as first, open(second_path, "rb") as second:
            while True:
                first_chunk = first.read(self.chunk_size)
                second_chunk = second.read(self.chunk_size)
                if first_chunk != second_chunk:
                    return False
                if not first_chunk:
                    return True

    def _remove_path_from_tree(self, group_id, path):
        for child in self.tree.get_children(group_id):
            if not self._is_file_item(child):
                continue
            vals = self.tree.item(child, "values")
            if vals and vals[2] == path:
                self.tree.delete(child)
                return

    def _update_group_header(self, group_id, paths):
        try:
            size = os.path.getsize(paths[0])
        except OSError:
            size = 0
        wasted = size * (len(paths) - 1)
        text = f"{len(paths)} dosya · {self._format_size(size)} each · Boşluk: {self._format_size(wasted)}"
        self.tree.item(group_id, text=text)

    def _update_stats_after_delete(self):
        remaining = 0
        groups = 0
        dupe_count = 0
        wasted = 0
        for paths in self.group_items.values():
            if len(paths) < 2:
                continue
            groups += 1
            dupe_count += len(paths) - 1
            remaining += len(paths)
            try:
                wasted += os.path.getsize(paths[0]) * (len(paths) - 1)
            except OSError:
                pass
        self.stats_var.set(f"Dosya: {remaining} | Kopya Grupları: {groups} | Toplam Kopya: {dupe_count} | Boşluk: {self._format_size(wasted)}")

    def _export_results(self):
        if not self.group_items:
            messagebox.showinfo("Bilgi", "Dışa aktarılacak veri yok.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv"), ("Tüm Dosyalar", "*.*")]
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Grup", "Dosya Adı", "Yol", "Boyut", "Değiştirilme", "Sakla"])
                    for group_id, paths in self.group_items.items():
                        group_text = self.tree.item(group_id, "text")
                        keep_path = self.group_keep_paths.get(group_id)
                        for path in paths:
                            try:
                                stat = os.stat(path)
                            except OSError:
                                continue
                            writer.writerow([
                                group_text,
                                os.path.basename(path),
                                path,
                                self._format_size(stat.st_size),
                                self._format_time(stat.st_mtime),
                                "☑" if path == keep_path else "☐"
                            ])
            else:
                data = []
                for group_id, paths in self.group_items.items():
                    group_text = self.tree.item(group_id, "text")
                    files = []
                    keep_path = self.group_keep_paths.get(group_id)
                    for path in paths:
                        try:
                            stat = os.stat(path)
                        except OSError:
                            continue
                        files.append({
                            "name": os.path.basename(path),
                            "path": path,
                            "size": self._format_size(stat.st_size),
                            "modified": self._format_time(stat.st_mtime),
                            "keep": path == keep_path
                        })
                    data.append({"group": group_text, "files": files})
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Başarılı", f"Sonuçlar kaydedildi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarma başarısız: {e}")


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = DuplicateFinder(root)
    root.mainloop()


if __name__ == "__main__":
    main()
