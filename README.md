# VibeController

Hastily vibecoded util for automated ESP32 webflasher versioning.

put firmwares in /fw/{NNN}. Example entry:

``` bash
├── fw
│   ├── 121
│   │   ├── filesystem.bin
│   │   ├── firmware.bin
│   │   └── fullimage.bin
```


## Next steps

* add automated filesystem generator
* automatically merge filesystem and firmware into full image, using some config preset
* relative / absolute / hardcoded paths, add nginx example config