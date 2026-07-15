#!/bin/bash

echo "🔧 Configurazione ambiente Python 3.12..."

# Aggiunta PATH
if ! grep -q "/usr/local/python/3.12.1/bin" ~/.bashrc; then
    echo 'export PATH="/usr/local/python/3.12.1/bin:$PATH"' >> ~/.bashrc
    echo "✔ PATH aggiornato"
else
    echo "✔ PATH già configurato"
fi

# Alias python e pip
if ! grep -q "alias python=" ~/.bashrc; then
    echo 'alias python="python3.12"' >> ~/.bashrc
    echo "✔ Alias python creato"
else
    echo "✔ Alias python già presente"
fi

if ! grep -q "alias pip=" ~/.bashrc; then
    echo 'alias pip="pip3.12"' >> ~/.bashrc
    echo "✔ Alias pip creato"
else
    echo "✔ Alias pip già presente"
fi

# Ricarica configurazione
source ~/.bashrc

# Aggiorna pip
python3.12 -m pip install --upgrade pip

echo "🔍 Verifica:"
echo "python → $(which python)"
echo "pip → $(which pip)"
python --version
pip --version

echo "🎉 Configurazione completata!"
