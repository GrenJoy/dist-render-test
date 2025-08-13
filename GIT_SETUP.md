# Настройка Git репозитория для disc-render

## Автоматическая настройка

### Вариант 1: Batch файл (Windows)
1. Дважды кликните на `setup_git.bat`
2. Следуйте инструкциям в командной строке

### Вариант 2: PowerShell скрипт
1. Откройте PowerShell от имени администратора
2. Перейдите в папку проекта
3. Выполните: `.\setup_git.ps1`

## Ручная настройка

### 1. Установите Git
Если Git не установлен, скачайте с [https://git-scm.com/](https://git-scm.com/)

### 2. Инициализируйте репозиторий
```bash
git init
```

### 3. Добавьте удаленный репозиторий
```bash
git remote add origin https://github.com/GrenJoy/disc-render.git
```

### 4. Добавьте все файлы
```bash
git add .
```

### 5. Сделайте первый коммит
```bash
git commit -m "Initial commit: Fix deployment compatibility issues"
```

### 6. Установите upstream ветку
```bash
git branch -M main
git push -u origin main
```

## Проверка статуса
```bash
git status
git remote -v
```

## Полезные команды
- `git add .` - добавить все изменения
- `git commit -m "message"` - закоммитить изменения
- `git push origin main` - запушовать в GitHub
- `git pull origin main` - скачать изменения с GitHub
