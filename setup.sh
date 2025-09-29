#!/bin/bash
# ServeBeer IPFS CDN - Setup Script (Fixed)
# Automatycznie konfiguruje środowisko dla aplikacji

set -e

echo "🍺 ServeBeer IPFS CDN - Setup Script"
echo "=================================="

# Sprawdź wymagania systemowe
check_requirements() {
    echo "🔍 Sprawdzanie wymagań systemowych..."
    
    # Python 3.8+
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 nie jest zainstalowany"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    version_check=$(python3 -c "import sys; print(1 if sys.version_info >= (3, 8) else 0)")
    
    if [ "$version_check" == "0" ]; then
        echo "❌ Wymagany Python 3.8+, masz $python_version"
        exit 1
    fi
    
    echo "✅ Python $python_version"
    
    # pip
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip nie jest zainstalowany"
        exit 1
    fi
    
    echo "✅ pip jest dostępny"
    
    # Git (opcjonalne)
    if command -v git &> /dev/null; then
        echo "✅ Git jest dostępny"
    else
        echo "⚠️  Git nie jest zainstalowany (opcjonalne)"
    fi
}

# Stwórz środowisko wirtualne
setup_virtualenv() {
    echo "🐍 Konfiguracja środowiska wirtualnego..."
    
    if [ -d "venv" ]; then
        echo "📁 Środowisko wirtualne już istnieje"
        read -p "Chcesz je odtworzyć? (y/N): " recreate
        if [[ $recreate =~ ^[Yy]$ ]]; then
            echo "🗑️ Usuwam stare środowisko..."
            rm -rf venv
        else
            echo "✅ Używam istniejącego środowiska"
            return
        fi
    fi
    
    echo "📦 Tworzę nowe środowisko wirtualne..."
    python3 -m venv venv
    
    # Aktywuj venv
    source venv/bin/activate
    
    # Upgrade pip
    echo "⬆️ Aktualizuję pip..."
    pip install --upgrade pip
    
    echo "✅ Środowisko wirtualne utworzone"
}

# Zainstaluj dependencje
install_dependencies() {
    echo "📦 Instalacja dependencji..."
    
    # Aktywuj venv jeśli nie jest aktywny
    if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        else
            echo "❌ Środowisko wirtualne nie znalezione. Uruchom setup ponownie."
            exit 1
        fi
    fi
    
    echo "⬇️ Instaluję pakiety Python..."
    pip install -r requirements.txt
    
    echo "✅ Dependencje zainstalowane"
}

# Konfiguruj środowisko
setup_environment() {
    echo "⚙️  Konfiguracja środowiska..."
    
    # Stwórz katalogi
    echo "📁 Tworzę katalogi..."
    mkdir -p database logs static/uploads templates
    
    # Skopiuj .env.example do .env jeśli nie istnieje
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "📝 Utworzony plik .env z szablonu"
            echo "⚠️  WAŻNE: Edytuj plik .env i ustaw swoje wartości!"
        else
            echo "⚠️  Plik .env.example nie istnieje, tworzę podstawowy .env"
            create_basic_env
        fi
    else
        echo "📁 Plik .env już istnieje"
    fi
    
    echo "✅ Katalogi i pliki konfiguracyjne utworzone"
}

# Stwórz podstawowy plik .env jeśli .env.example nie istnieje
create_basic_env() {
    cat > .env << 'EOF'
# ServeBeer IPFS CDN - Basic Environment Configuration
SECRET_KEY=change-this-in-production-guerrilla-node-secret-key
TESTING_MODE=True
IPFS_API_URL=http://localhost:5001/api/v0
DATABASE_PATH=database/servebeer.db
HOST=0.0.0.0
PORT=5000
EOF
    echo "✅ Utworzony podstawowy plik .env"
}

# Inicjalizuj bazę danych
init_database() {
    echo "🗄️ Inicjalizacja bazy danych..."
    
    # Aktywuj venv jeśli nie jest aktywny
    if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
        source venv/bin/activate
    fi
    
    python3 -c "
try:
    from app import init_database
    init_database()
    print('✅ Baza danych zainicjalizowana')
except Exception as e:
    print(f'⚠️  Błąd inicjalizacji bazy danych: {e}')
    print('💡 Będzie utworzona przy pierwszym uruchomieniu aplikacji')
"
}

# Sprawdź IPFS
check_ipfs() {
    echo "🌐 Sprawdzanie połączenia z IPFS..."
    
    if curl -s --connect-timeout 3 http://localhost:5001/api/v0/version > /dev/null 2>&1; then
        echo "✅ IPFS daemon działa"
        # Sprawdź wersję IPFS
        ipfs_version=$(curl -s http://localhost:5001/api/v0/version | grep -o '"Version":"[^"]*' | cut -d'"' -f4)
        echo "📟 IPFS wersja: $ipfs_version"
    else
        echo "⚠️  IPFS daemon nie działa na localhost:5001"
        echo "💡 Uruchom IPFS daemon:"
        echo "   ipfs daemon"
        echo ""
        echo "📚 Jeśli nie masz IPFS:"
        echo "   • Ubuntu/Debian: sudo apt install ipfs"
        echo "   • Mac: brew install ipfs"
        echo "   • Ręczna instalacja: https://docs.ipfs.io/install/"
        echo ""
        echo "🔄 Po instalacji uruchom:"
        echo "   ipfs init"
        echo "   ipfs daemon"
    fi
}

# Testuj aplikację
test_application() {
    echo "🧪 Test aplikacji..."
    
    if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Test importu
    python3 -c "
try:
    import flask
    print('✅ Flask zaimportowany')
    import requests
    print('✅ Requests zaimportowany')
    import sqlite3
    print('✅ SQLite3 dostępny')
    
    # Test basic app structure
    from app import app
    print('✅ Aplikacja ServeBeer importuje się poprawnie')
    
except ImportError as e:
    print(f'❌ Błąd importu: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Ostrzeżenie: {e}')
"
    
    echo "✅ Podstawowe testy przeszły"
}

# Pokaż instrukcje końcowe
show_final_instructions() {
    echo ""
    echo "🎉 Setup zakończony pomyślnie!"
    echo "=============================="
    echo ""
    echo "📋 Następne kroki:"
    echo "1. 📝 Edytuj plik .env z własnymi ustawieniami"
    echo "2. 🌐 Uruchom IPFS daemon: ipfs daemon"
    echo "3. 🐍 Aktywuj środowisko: source venv/bin/activate"
    echo "4. 🚀 Uruchom aplikację: python app.py"
    echo "5. 🌍 Otwórz http://localhost:5000 w przeglądarce"
    echo ""
    echo "🔧 Użyteczne komendy:"
    echo "• 🩺 Status zdrowia: curl http://localhost:5000/health"
    echo "• 📊 Status systemu: http://localhost:5000/status"
    echo "• 🧪 Testy: python -m pytest (po instalacji)"
    echo ""
    echo "🔗 IPFS Gateway:"
    echo "• Lokalny: http://localhost:8080/ipfs/[CID]"
    echo "• Publiczny: https://ipfs.io/ipfs/[CID]"
    echo ""
    echo "📁 Struktura katalogów:"
    echo "• database/ - baza danych SQLite"  
    echo "• logs/ - logi aplikacji i audytu"
    echo "• static/ - pliki statyczne"
    echo ""
    echo "🐛 W razie problemów:"
    echo "• Sprawdź logi w logs/servebeer_audit.log"
    echo "• Zweryfikuj czy IPFS daemon działa: ipfs swarm peers"
    echo "• Test health check: curl http://localhost:5000/health"
    echo ""
    echo "🍺⚡ ServeBeer IPFS CDN - Gotowe do akcji!"
    echo "💪 Guerrilla Infrastructure is ready!"
}

# Główna funkcja
main() {
    check_requirements
    setup_virtualenv
    install_dependencies
    setup_environment
    init_database
    check_ipfs
    test_application
    show_final_instructions
}

# Obsłuż argumenty wiersza poleceń
case "${1:-}" in
    --quick)
        echo "⚡ Tryb szybki - podstawowy setup"
        setup_virtualenv
        install_dependencies
        setup_environment
        echo "✅ Szybki setup zakończony"
        ;;
    --help|-h)
        echo "Użycie: $0 [--quick|--help]"
        echo "  --quick   Szybka instalacja"
        echo "  --help    Pokaż pomoc"
        ;;
    *)
        main
        ;;
esac
