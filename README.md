<div align="center">
  
  # <img src="https://i.imgur.com/PABzg9J.jpeg" width="40" height="40" style="vertical-align: middle;"> RyujinApp

  <a href="https://github.com/Ryujin-K/RyujinApp">
    <img width="500" src="https://i.imgur.com/EWWKqIw.png" alt="RyujinApp Logo" />
  </a>
  
  **A powerful cross-platform manga downloader**
  
  Fast, reliable, and feature-rich manga downloading for Linux and Windows
  
  [![Download](https://img.shields.io/badge/Download-Latest_Release-blue.svg?style=for-the-badge)](https://github.com/Ryujin-K/RyujinApp/releases)
  [![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/zhfWRqYY6B)
  
  [![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg?style=flat-square)](https://github.com/Ryujin-K/RyujinApp/releases)
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![License](https://img.shields.io/github/license/Ryujin-K/RyujinApp?style=flat-square)](LICENSE)
  
</div>

---

## ✨ Features

- 🚀 **High-speed downloads** with advanced image processing
- 🔄 **Smart image slicing** powered by SmartStitch technology
- 🌐 **Multi-platform support** for Linux and Windows
- 🎨 **Modern GUI** built with Qt
- 📚 **Multiple manga sources** support
- 🔧 **Developer-friendly** with easy provider creation

## 🚀 Quick Start

### 📥 Installation

#### 🪟 Windows
1. **Download** the `.exe` file from [Releases](https://github.com/Ryujin-K/RyujinApp/releases)
2. **Run** the executable directly
3. **Enjoy!** No additional setup required

#### 🐧 Linux
1. **Download** the Linux executable from [Releases](https://github.com/Ryujin-K/RyujinApp/releases)
2. **Make executable**: `chmod +x RyujinApp-linux`
3. **Run**: `./RyujinApp-linux`

> ⚠️ **Note**: Chrome browser is still required for web scraping functionality

## 🔧 System Requirements

### 🌐 Global Dependencies
- **Chrome Browser** - Required for web scraping functionality

### 🐧 Linux/BSD Specific

#### KDE Desktop Environment
- ✅ **Native support** - Usually works out of the box
- Requires: `dbus`, `klipper`, and `dbus-python` (typically pre-installed)

#### X11 Window System
Install clipboard utilities:
```bash
# Option 1: xsel
sudo zypper install xsel

# Option 2: xclip  
sudo zypper install xclip
```

#### Wayland Display Server
Install Wayland clipboard support:
```bash
sudo zypper install wl-clipboard
```

## 💻 Development Commands

```bash
poetry install    # 📦 Install all dependencies
poetry run start  # 🚀 Start the application
poetry run build  # 🔨 Build the project for distribution
poetry run clean  # 🧹 Clean __pycache__ files
poetry run new    # ➕ Create a new provider
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. 🍴 **Fork** the repository
2. 🌿 **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. 📤 **Push** to the branch (`git push origin feature/amazing-feature`)
5. 🔀 **Open** a Pull Request

## 📜 Credits & Acknowledgments

This project stands on the shoulders of giants. Special thanks to:

- 🔥 **[Pyneko](https://github.com/Lyem/Pyneko)** - Foundation for GUI and web scraping functionality
- 🧩 **[SmartStitch](https://github.com/MechTechnology/SmartStitch)** - Advanced image slicing capabilities
- 👑 **[HakuNeko](https://github.com/manga-download/hakuneko)** - Original inspiration and methodology

## 📞 Support & Community

- 💬 **Discord**: [Join our community](https://discord.gg/zhfWRqYY6B)
- 🐛 **Issues**: [Report bugs or request features](https://github.com/Ryujin-K/RyujinApp/issues)
- 📖 **Releases**: [Download the latest version](https://github.com/Ryujin-K/RyujinApp/releases)

---

<div align="center">
    
  ⭐ **Star this repository if you found it helpful!**
  
</div>
