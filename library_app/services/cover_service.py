import os
from PIL import Image

def _get_pymupdf():
    """Ленивый импорт с безопасной регистрацией путей для DLL"""
    app_dir = os.path.dirname(os.path.abspath(__file__))  # Папка текущего файла
    # Для скомпилированного .exe берём папку рядом с exe
    if getattr(os, "path", None) and hasattr(os, "add_dll_directory"):
        # Nuitka кладёт exe и DLL в одну папку, либо в .dist/
        exe_dir = os.path.dirname(os.path.abspath(__import__('sys').executable))
        
        for dll_dir in [exe_dir, os.path.join(exe_dir, "pymupdf")]:
            if os.path.isdir(dll_dir):
                try:
                    os.add_dll_directory(dll_dir)
                except OSError:
                    pass
                    
    import pymupdf
    return pymupdf

def create_cover_from_pdf(pdf_path, img_dir):
    if not pdf_path or not os.path.exists(pdf_path):
        return ""
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    cover_filename = f"{base_name}_auto.png"
    cover_path = os.path.join(img_dir, cover_filename)
    
    if os.path.exists(cover_path):
        return cover_filename
        
    try:
        fitz = _get_pymupdf()
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((120, 164), Image.Resampling.LANCZOS)
        img.save(cover_path, "PNG")
        doc.close()
        return cover_filename
    except Exception as e:
        # В релизе можно убрать print или заменить на logging
        print(f"Ошибка создания обложки для {pdf_path}: {e}")
        return ""