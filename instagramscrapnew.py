from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import instaloader
from datetime import datetime
import os
import zipfile
from pathlib import Path

root = Tk()
root.geometry("450x650")
root.configure(background='#1a1a1a')
root.resizable(False, False)
root.title("InStalker")

# Variabel
link = StringVar()
year_filter = StringVar()
status_label = None

def compress_media_files(username):
    """Compress video dan gambar berdasarkan tanggal post"""
    profile_folder = Path(username)
    
    if not profile_folder.exists():
        return 0
    
    media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                       '.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    # Kelompokkan file berdasarkan tanggal dari nama file
    # Format nama file instaloader: YYYY-MM-DD_HH-MM-SS_UTC.ext
    date_groups = {}
    
    for file in profile_folder.iterdir():
        if file.is_file() and file.suffix.lower() in media_extensions:
            try:
                # Ambil tanggal dari nama file (10 karakter pertama: YYYY-MM-DD)
                date_str = file.name[:10]
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(file)
            except:
                continue
    
    total_compressed = 0
    
    # Buat zip untuk setiap tanggal
    for date_str, files in date_groups.items():
        zip_path = profile_folder / f"media_{date_str}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                zipf.write(file, file.name)
                file.unlink()  # Hapus file asli
                total_compressed += 1
    
    return total_compressed

def extract_post_urls(username):
    """Extract URLs dari post dan simpan per file berdasarkan tanggal"""
    profile_folder = Path(username)
    
    if not profile_folder.exists():
        return 0
    
    import json
    import lzma
    url_count = 0
    
    # Baca dari file JSON dan JSON.XZ (metadata Instaloader)
    json_files = list(profile_folder.glob("*.json")) + list(profile_folder.glob("*.json.xz"))
    
    for json_file in json_files:
        try:
            # Baca file JSON
            if json_file.suffix == '.xz':
                with lzma.open(json_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Ekstrak shortcode dan tanggal
            shortcode = None
            date_str = None
            
            if 'node' in data:
                node = data['node']
                shortcode = node.get('shortcode')
                # Tanggal dari timestamp
                if 'taken_at_timestamp' in node:
                    from datetime import datetime
                    timestamp = node['taken_at_timestamp']
                    date_obj = datetime.fromtimestamp(timestamp)
                    date_str = date_obj.strftime('%Y-%m-%d')
            
            # Jika tidak ada, coba ambil dari nama file
            if not date_str:
                filename = json_file.stem.replace('.json', '')
                # Format: YYYY-MM-DD_HH-MM-SS_UTC
                if '_' in filename:
                    date_str = filename.split('_')[0]
            
            if shortcode and date_str:
                url = f"https://www.instagram.com/p/{shortcode}/"
                
                # Buat file URL
                url_file = profile_folder / f"{date_str}_{shortcode}_url.txt"
                
                with open(url_file, 'w', encoding='utf-8') as f:
                    f.write(url)
                
                url_count += 1
                
        except Exception as e:
            continue
    
    return url_count

def download_data():
    global status_label
    
    username = link.get().strip()
    if not username:
        messagebox.showwarning("Warning", "Masukkan username Instagram!")
        return
    
    # Hapus status label sebelumnya
    if status_label:
        status_label.destroy()
    
    # Status downloading
    status_label = Label(root, text="Downloading...", font=("Segoe UI", 11), 
                        fg="#FFA500", bg="#1a1a1a")
    status_label.place(x=175, y=480)
    root.update()
    
    download_success = False
    
    try:
        L = instaloader.Instaloader()
        
        # Filter tahun jika dipilih
        selected_year = year_filter.get()
        if selected_year and selected_year != "Semua":
            year = int(selected_year)
            try:
                L.download_profile(username, profile_pic_only=False,
                                 post_filter=lambda post: post.date.year == year)
            except KeyboardInterrupt:
                # User menekan Ctrl+C atau limit tercapai
                pass
            except instaloader.exceptions.QueryReturnedForbiddenException:
                # Error 403, tapi lanjutkan proses
                pass
            except instaloader.exceptions.ConnectionException:
                # Error koneksi, tapi lanjutkan proses
                pass
        else:
            try:
                L.download_profile(username, profile_pic_only=False)
            except KeyboardInterrupt:
                pass
            except instaloader.exceptions.QueryReturnedForbiddenException:
                pass
            except instaloader.exceptions.ConnectionException:
                pass
        
        download_success = True
        
    except Exception as e:
        # Error fatal lainnya
        status_label.config(text="✗ Download Gagal!", fg="#ff0000")
        messagebox.showerror("Error", f"Error: {str(e)}")
        return
    
    # Lanjutkan proses meskipun download tidak sempurna
    if download_success:
        try:
            # Extract post URLs
            status_label.config(text="Extracting post URLs...", fg="#FFA500")
            root.update()
            
            url_count = extract_post_urls(username)
            
            # Compress media files
            status_label.config(text="Compressing media files...", fg="#FFA500")
            root.update()
            
            compressed_count = compress_media_files(username)
            
            status_label.config(text="✓ Proses Selesai!", fg="#00ff00")
            
            success_msg = f"Data tersimpan di folder: {username}\n"
            success_msg += "⚠️ Download mungkin tidak lengkap (limit/error)\n"
            if url_count > 0:
                success_msg += f"✓ {url_count} URL post disimpan ke post_urls.txt\n"
            if compressed_count > 0:
                success_msg += f"✓ {compressed_count} file media di-compress ke media.zip"
            
            messagebox.showinfo("Success", success_msg)
            
        except Exception as e:
            status_label.config(text="✓ Download selesai (error saat kompresi)", fg="#FFA500")
            messagebox.showwarning("Warning", 
                                 f"Download selesai tapi ada error saat kompresi:\n{str(e)}")

# Header
header_frame = Frame(root, bg="#2d2d2d", height=80)
header_frame.pack(fill=X)
header_frame.pack_propagate(False)

Label(header_frame, text="InStalker", font=("Segoe UI", 28, "bold"), 
      fg="#ffffff", bg="#2d2d2d").pack(pady=20)

# Content Frame
content_frame = Frame(root, bg="#1a1a1a")
content_frame.pack(pady=40, padx=40, fill=BOTH, expand=True)

# Username Section
Label(content_frame, text="Username Instagram", font=("Segoe UI", 12), 
      fg="#b0b0b0", bg="#1a1a1a").pack(anchor=W, pady=(0, 8))

username_entry = Entry(content_frame, textvariable=link, font=("Segoe UI", 12),
                      bg="#2d2d2d", fg="#ffffff", relief=FLAT, 
                      insertbackground="white", bd=0)
username_entry.pack(fill=X, ipady=10, pady=(0, 25))
username_entry.config(highlightthickness=1, highlightbackground="#404040", 
                     highlightcolor="#5c9dff")

# Year Filter Section
Label(content_frame, text="Filter Tahun (Opsional)", font=("Segoe UI", 12), 
      fg="#b0b0b0", bg="#1a1a1a").pack(anchor=W, pady=(0, 8))

current_year = datetime.now().year
years = ["Semua"] + [str(year) for year in range(current_year, 2009, -1)]

year_combo = ttk.Combobox(content_frame, textvariable=year_filter, 
                         values=years, font=("Segoe UI", 11), state="readonly")
year_combo.pack(fill=X, ipady=8, pady=(0, 35))
year_combo.set("Semua")

# Style untuk combobox
style = ttk.Style()
style.theme_use('clam')
style.configure("TCombobox", 
                fieldbackground="#2d2d2d",
                background="#2d2d2d",
                foreground="#ffffff",
                arrowcolor="#ffffff",
                bordercolor="#404040")

# Download Button
download_btn = Button(content_frame, text="DOWNLOAD DATA", 
                     font=("Segoe UI", 13, "bold"), bg="#5c9dff", 
                     fg="#ffffff", relief=FLAT, cursor="hand2",
                     activebackground="#4a8eeb", activeforeground="#ffffff",
                     command=download_data)
download_btn.pack(fill=X, ipady=12)

# Info Label
info_text = "Masukkan username Instagram target\nPilih tahun untuk memfilter post (opsional)"
Label(content_frame, text=info_text, font=("Segoe UI", 9), 
      fg="#808080", bg="#1a1a1a", justify=CENTER).pack(pady=(30, 0))

# Footer
Label(root, text="© 2025 bimsky", font=("Segoe UI", 9), 
      fg="#606060", bg="#1a1a1a").pack(side=BOTTOM, pady=15)

root.mainloop()
