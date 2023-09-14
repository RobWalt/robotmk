iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
choco install -y googlechrome
choco install -y python
choco install -y nushell
choco install -y sysinternals
choco install -y vscode
choco install -y git.install

(new-object net.webclient).DownloadFile("https://nightly.link/elabit/robotmk/actions/artifacts/878920132.zip", "C:\Users\vagrant\Downloads\rcc.zip")
Expand-Archive "C:\Users\vagrant\Downloads\rcc.zip" -Force -DestinationPath "C:\Users\vagrant\Downloads\"
Copy-Item "C:\Users\vagrant\Downloads\windows64\rcc.exe" -Destination "C:\Users\vagrant\AppData\Local\Microsoft\WindowsApps\rcc.exe"
rcc configure identity --do-not-track

python -m pip install -e "C:\robotmk\"
