#!/bin/bash

# Устанавливаем переменные
REPO_URL="https://github.com/Yaromo/S_pad"
TARGET_DIR="$HOME/S_pad"

echo "🚀 Начинаем автоматическую установку S_pad..."

# 1. Проверяем, установлен ли git
if ! command -v git &>/dev/null; then
    echo "❌ Ошибка: git не установлен в вашей системе."
    echo "Пожалуйста, установите git с помощью вашего пакетного менеджера (например: sudo apt install git или sudo pacman -S git) и запустите скрипт снова."
    exit 1
fi

# 2. Создаем директорию и скачиваем файлы
if [ -d "$TARGET_DIR" ]; then
    echo "📦 Папка $TARGET_DIR уже существует."
    echo "🔄 Обновляем файлы из репозитория..."
    cd "$TARGET_DIR" || exit 1
    
    # Если папка уже есть и это git-репозиторий — подтягиваем изменения
    if [ -d ".git" ]; then
        git pull
    else
        echo "⚠ Папка не является git-репозиторием. Очищаем и клонируем заново..."
        cd "$HOME" || exit 1
        rm -rf "$TARGET_DIR"
        git clone "$REPO_URL" "$TARGET_DIR"
    fi
else
    echo "📂 Создаем папку $TARGET_DIR и клонируем репозиторий..."
    git clone "$REPO_URL" "$TARGET_DIR"
fi

# 3. Переходим в папку проекта
cd "$TARGET_DIR" || exit 1

if [ -f "clear.sh" ]; then
    echo "🧹 Файл clean.sh найден. Выдаем права на исполнение..."
    chmod +x clear.sh
fi

# 4. Проверяем наличие start.sh и запускаем его
if [ -f "start.sh" ]; then
    echo "✅ Файл start.sh найден. Выдаем права на запуск..."
    chmod +x start.sh
    
    echo "🖥️ Запуск приложения через start.sh..."
    echo "------------------------------------------------"
    ./start.sh
else
    echo "❌ КРИТИЧЕСКАЯ ОШИБКА: Файл start.sh не найден в скачанном репозитории!"
    exit 1
fi

