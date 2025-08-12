# RyujinApp  
<div align="center">
  <a href="https://github.com/Ryujin-K/RyujinApp">
    <img width="450" src="https://i.imgur.com/RWMFT6o.png" />
    <img width="450" src="https://i.imgur.com/EWWKqIw.png" />
  </a>
</div>

A cross-platform manga downloader for **Linux and Windows**, using [Pyneko](https://github.com/Lyem/Pyneko) base code, that´s  based on [HakuNeko](https://github.com/manga-download/hakuneko). It incorporates code from **SmartStitch** for advanced image slicing, ensuring fast and seamless downloads.

## Dependencies  

🌎 **Global**: Chrome  

🐧 **Linux/BSD**:  
  - **KDE**: Native support (requires `dbus`, `klipper`, and `dbus-python`, usually pre-installed).  
  - **X11**: Install `xsel` or `xclip`  
    ```bash
    sudo zypper install xsel  # or  
    sudo zypper install xclip  
    ```  
  - **Wayland**: Install `wl-clipboard`  
    ```bash
    sudo zypper install wl-clipboard  
    ```

## Development Commands
 
```bash
poetry install    # Install dependencies  
poetry run start  # Start the application  
poetry run build  # Build the project  
poetry run clean  # Clean __pycache__  
poetry run new    # Create a new provider  
```

## Credits

- This project uses code from the [Pyneko](https://github.com/MechTechnology/SmartStitch) for GUI and scrapping.
- This project uses code from the [SmartStitch](https://github.com/MechTechnology/SmartStitch) for image slicing.
