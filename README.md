<div align="center">
  
# <img src="https://i.imgur.com/PABzg9J.jpeg" width="40" height="40" style="vertical-align: middle;"> RyujinApp

<a href="https://github.com/Ryujin-K/RyujinApp">
  <img width="500" src="https://i.imgur.com/EWWKqIw.png" alt="RyujinApp Logo" />
</a>

**Cross-platform Manga Downloader**  
_Windows and Linux_

[![Download](https://img.shields.io/badge/Download-Latest_Release-blue.svg?style=for-the-badge)](https://github.com/Ryujin-K/RyujinApp/releases)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/cTa5WbEsfS)
[![Fork](https://img.shields.io/github/forks/Ryujin-K/RyujinApp?style=for-the-badge&logo=github)](https://github.com/Ryujin-K/RyujinApp/fork)


[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg?style=flat-square)](https://github.com/Ryujin-K/RyujinApp/releases)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ryujin-K/RyujinApp?style=flat-square)](LICENSE)

</div>

---

## ✨ Features

- **High-speed downloads** with optimized image processing  
- **Smart image slicing** powered by SmartStitch technology  
- **Multi-platform support** (Linux & Windows)  
- **Modern GUI** built with Qt  
- **Multiple manga sources** integrated  
- **Developer-friendly** provider creation system  

---

## 🚀 Quick Start

### Windows
1. Download the `.exe` file from [Releases](https://github.com/Ryujin-K/RyujinApp/releases)  
2. Run the executable  
3. Done! No additional setup required  

### Linux
1. Download **RyujinApp** (the file without `.exe`) from [Releases](https://github.com/Ryujin-K/RyujinApp/releases)  
2. Make it executable:  
   ```bash
   chmod +x RyujinApp
   ```  
3. Run:  
   ```bash
   ./RyujinApp
   ```

> **Note**: Chrome browser is required for scraping.

---

## ⚙️ System Requirements

### Global
- **Chrome Browser** (mandatory for web scraping)

### Linux/BSD Specific

**KDE Desktop**  
- Works out of the box (requires `dbus`, `klipper`, and `dbus-python`, usually pre-installed)  

**X11 Systems** – install clipboard tools:
```bash
sudo zypper install xsel
# or
sudo zypper install xclip
```

**Wayland** – install clipboard support:
```bash
sudo zypper install wl-clipboard
```

---

## 💻 Development

```bash
poetry install    # Install dependencies
poetry run start  # Start the application
poetry run build  # Build the application
poetry run clean  # Clean pycache files
poetry run new    # Create a new provider
```

---

## 🤝 Contributing

If you want to contribute with code, the best way is to:  

**Fork this repository**

All support discussions happen in our **Discord community**.  

Whether you want to:  
- Report a bug  
- Suggest a feature  
- Get help setting up   

👉 Join us here: [RyujinApp Community](https://discord.com/invite/cTa5WbEsfS)

---

## 📜 Credits & Acknowledgments

This project is built upon the amazing work of:  

- [Pyneko](https://github.com/Lyem/Pyneko) – GUI & scraping foundation, my personal inspiration

- [SmartStitch](https://github.com/MechTechnology/SmartStitch)

- [HakuNeko](https://github.com/manga-download/hakuneko)

---

## 📞 Community & Support

- Join our [Discord Community](https://discord.com/invite/cTa5WbEsfS) for support, discussions and announcements  
- Fork this repository to experiment or add your own features  
- Download the latest release from [Releases](https://github.com/Ryujin-K/RyujinApp/releases)  

---

<div align="center">
  
⭐ **If you enjoy RyujinApp, give it a star and fork the project!**

</div>
