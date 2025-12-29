# Smart-Duplicate-Cleaner

**Duplicate File Finder & Remover (Hash-based)** ✅

A small Python tool with a simple Tkinter GUI that detects duplicate files inside a selected folder using SHA-256 file hashing and can optionally permanently delete duplicates.

---

## Features ✨

- Recursively scans all subfolders in the selected directory.
- Detects duplicates by hashing file contents using SHA-256.
- Lists each duplicate set in the GUI output area.
- After user confirmation, keeps one file from each set and permanently deletes the others.
- Memory-efficient hashing via chunked reads for large files.

## Requirements 🔧

- Python 3.8 or newer (tested with 3.14)
- Tkinter (for the GUI; typically available on Windows)

> On Linux: install with `sudo apt install python3-tk`.

## Installation & Running 🚀

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd Smart-Duplicate-Cleaner
   ```

2. Run the application:

   ```bash
   python main.py
   ```

## Usage 🖱️

1. Click **"Open Folder"** to choose the folder to scan.
2. Click **"Start"** to begin scanning.
3. Review the duplicate sets displayed in the output area.
4. Click **"Delete Duplicates"** and confirm to permanently remove duplicates (this action is **irreversible**).

## How it works 💡

- Each file is read in chunks (default 8192 bytes) and hashed with SHA-256.
- Files with identical hashes are considered duplicates.
- During deletion, the first file in each duplicate set is preserved; the rest are removed with `os.remove()`.

## Safety & Warnings ⚠️

- **Deletions are permanent.** Please back up important data before running the deletion.
- Duplicates are determined by file content only: files with different names but identical content are considered duplicates.

## Troubleshooting / Help 🛠️

- If the GUI does not open or you see `tkinter` errors, ensure tkinter is installed on your system.
- Scanning large directories may take time—please be patient.

## Contributing 🤝

Contributions, bug fixes, and suggestions are welcome via pull requests or issues.

## License 📄

This project is licensed under the MIT License. (Change this if you prefer a different license.)

---

**Note:** If you'd like additional changes—an English/Turkish bilingual README, screenshots, or more detailed instructions—let me know and I can add them.

## ⚠️ **⛔ WARNING — IMPORTANT**

> 🚨 **THIS APPLICATION PERMANENTLY DELETES FILES (IRREVERSIBLE)** 🚨
>
> - **Always BACK UP your data** before using this tool.
> - **The author is NOT RESPONSIBLE for any data loss.**
> - **Use this application AT YOUR OWN RISK.**
>
> **Recommendation:** First run a scan and carefully review duplicate files before using the delete function.

