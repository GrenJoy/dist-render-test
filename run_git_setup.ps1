# Простой скрипт для настройки git
Write-Host "Настройка Git репозитория..." -ForegroundColor Green

# Проверяем git
try {
    git --version
} catch {
    Write-Host "Git не установлен! Установите с https://git-scm.com/" -ForegroundColor Red
    exit
}

# Инициализируем репозиторий
Write-Host "Инициализация git..." -ForegroundColor Yellow
git init

# Добавляем remote
Write-Host "Добавление remote origin..." -ForegroundColor Yellow
git remote add origin https://github.com/GrenJoy/disc-render.git

# Добавляем файлы
Write-Host "Добавление файлов..." -ForegroundColor Yellow
git add .

# Коммитим
Write-Host "Создание коммита..." -ForegroundColor Yellow
git commit -m "Initial commit: Fix deployment compatibility issues"

# Устанавливаем ветку
Write-Host "Установка ветки main..." -ForegroundColor Yellow
git branch -M main

Write-Host "Готово! Теперь выполните: git push -u origin main" -ForegroundColor Green
