# Sahibinden Resim Çekici

Sahibinden.com ilan sayfasındaki tüm resimleri önizleyip tek tıkla indiren masaüstü uygulaması.

---
<img width="1042" height="750" alt="Ekran görüntüsü 2026-05-21 191451" src="https://github.com/user-attachments/assets/e9d779e0-750a-443a-b61e-3a0a71556b87" />

## Özellikler

- İlan sayfasının kaynak kodundan JPG resimleri otomatik algılar
- Thumbnail önizleme galerisi
- Resimlere tek tek veya toplu indirme
- Çift tıkla büyük önizleme penceresi
- Sağ tık menüsü

---

## Kurulum

Python 3.10 veya üzeri gereklidir.

```bash
pip install Pillow
```

---

## Kullanım

```bash
python sahibinden_resim_cekici.py
```

1. Sahibinden.com'da bir ilan sayfası aç
2. Sayfaya sağ tıkla → **Sayfa Kaynağını Görüntüle** — ya da — **Ctrl + U** bas
3. Açılan kaynak sayfasında **Ctrl + A** ile tümünü seç, **Ctrl + C** ile kopyala
4. Programdaki metin kutusuna **Ctrl + V** ile yapıştır
5. **▶ Çek** butonuna tıkla
6. Resimlere tıklayarak seç, **⬇ Seçilenleri İndir** ile kaydet

---

## Gereksinimler

| Paket | Sürüm |
|-------|-------|
| Python | 3.10+ |
| Pillow | herhangi |

Standart kütüphane dışında yalnızca **Pillow** gereklidir.

---

## Lisans

MIT
