# io.github.DamnedAngel.msx-tile-forge

Flatpak packaging for **MSX Tile Forge** targeting Linux systems

## Upstream Project repo

- Source: [https://github.com/DamnedAngel/msx-tile-forge](https://github.com/DamnedAngel/msx-tile-forge)

## User Guide

### How to install and run on Linux from Flathub

```bash
flatpak install flathub io.github.DamnedAngel.msx-tile-forge
flatpak run io.github.DamnedAngel.msx-tile-forge
```

## Developer Guide

If you're new about flathub, it's a good idea to read [submission](https://docs.flathub.org/docs/for-app-authors/submission), [maintenance](https://docs.flathub.org/docs/for-app-authors/maintenance) and [updates](https://docs.flathub.org/docs/for-app-authors/updates) guides. Also, see [python wheels](https://pypi.org/) if you need include more python dependencies into `flatpak/io.github.DamnedAngel.msx-tile-forge.yaml`.

### How to get Flathub project repo

1. Fork the [flathub project repo](https://github.com/flathub/io.github.DamnedAngel.msx-tile-forge);

2. Create a folder in your local machine;

3. Clone the repo files:  
   ```
   git clone https://github.com/<your_user_name>/io.github.DamnedAngel.msx-tile-forge.git
   ```

### How to do a local test on the [upstream project repo](https://github.com/DamnedAngel/msx-tile-forge)

1. Smoke test:  
   ```
   make -C flatpak smoketest
   ```

2. Full test (with linting):  
   ```
   make -C flatpak fulltest
   ```

### How to publish a new release into Flathub

1. Open the [upstream project repo](https://github.com/DamnedAngel/msx-tile-forge);
 
2. Open `flatpak/io.github.DamnedAngel.msx-tile-forge.metainfo.xml` and add a new `release version` row into `releases` tag;

3. Commit the change to the [upstream project repo](https://github.com/DamnedAngel/msx-tile-forge);

4. Open `flatpak/io.github.DamnedAngel.msx-tile-forge.yaml` and change `<release_version>`, `<release_tag_name>` and `<release_tag_commit_id>`;  
   ```
   - name: msx-tile-forge
     buildsystem: simple
     build-options:
       env:
         APP_VERSION: <release_version>
     sources:
       - type: git
         url: https://github.com/DamnedAngel/msx-tile-forge.git
         tag: <release_tag_name>
         commit: <release_tag_commit_id>
   ```

5. Do a smoke test on the [upstream project repo](https://github.com/DamnedAngel/msx-tile-forge):  
  ```
   make -C flatpak smoketest
  ```

6. Copy `flatpak/io.github.DamnedAngel.msx-tile-forge.yaml` from [upstream project repo](https://github.com/DamnedAngel/msx-tile-forge) to the [flathub project repo](https://github.com/flathub/io.github.DamnedAngel.msx-tile-forge);

7. Update [flathub project repo](https://github.com/flathub/io.github.DamnedAngel.msx-tile-forge) master branch:  
  ```
  git commit -m "Release <write_here_the_new_release_version>"
  git push origin master
  ```

8. Make a [PR](https://docs.flathub.org/docs/for-app-authors/updates#creating-updates) to the [flathub project repo](https://github.com/flathub/io.github.DamnedAngel.msx-tile-forge) master branch.

