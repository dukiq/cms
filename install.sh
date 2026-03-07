#!/bin/bash

set -e

cat << "EOF"
  .,-:::::  .        :   .::::::.
,;;;'````'  ;;,.    ;;; ;;;`    `
[[[         [[[[, ,[[[[,'[==/[[[[,
$$         $$$$"$$  '''    $
`88bo,__,o, 888 Y88" 888o88b    dP
  "YUMMMMMP"MMM  M'  "MMM "YMmMY"

EOF
echo ""

read -p "Введите директорию установки (/opt/cms): " INSTALL_DIR </dev/tty 2>/dev/null || true
INSTALL_DIR=${INSTALL_DIR:-/opt/cms}

echo ""
echo "Установка в: $INSTALL_DIR"
echo ""

if [ -d "$INSTALL_DIR" ]; then
    read -p "Директория существует. Удалить и переустановить? (y/n): " CONFIRM </dev/tty 2>/dev/null || CONFIRM="y"
    if [ "$CONFIRM" = "y" ] || [ -z "$CONFIRM" ]; then
        rm -rf "$INSTALL_DIR"
    else
        echo "Установка отменена"
        exit 1
    fi
fi

echo "Клонирование репозитория..."
git clone https://github.com/dukiq/cms "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo ""
echo "Проверка установки Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python не найден. Установка..."
    if command -v apt &> /dev/null; then
        apt update
        apt install -y python3 python3-venv python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    else
        echo "Невозможно установить Python. Установите вручную."
        exit 1
    fi
fi

echo ""
echo "Проверка установки Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Установка..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

echo ""
echo "Создание виртуального окружения..."
python3 -m venv venv

echo "Установка зависимостей..."
. venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Конфигурация"
echo "============"
read -p "Введите токен бота: " BOT_TOKEN </dev/tty 2>/dev/null || true
read -p "Введите ID администратора: " ADMIN_ID </dev/tty 2>/dev/null || true
read -sp "Введите пароль удаления: " DELETE_PASSWORD </dev/tty 2>/dev/null || true
echo ""

if [ -z "$BOT_TOKEN" ] || [ -z "$ADMIN_ID" ] || [ -z "$DELETE_PASSWORD" ]; then
    echo "Ошибка: не все параметры заданы"
    echo "Запустите скрипт напрямую: bash install.sh"
    exit 1
fi

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
DELETE_PASSWORD=$DELETE_PASSWORD
EOF

echo ""
echo "Установка systemd сервиса..."
sed "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" cmsdash.service > /tmp/cmsdash.service
cp /tmp/cmsdash.service /etc/systemd/system/cmsdash.service
rm /tmp/cmsdash.service

systemctl daemon-reload
systemctl enable cmsdash
systemctl start cmsdash

echo ""
echo "Установка завершена!"
echo ""
echo "Статус сервиса:"
systemctl status cmsdash --no-pager
echo ""
echo "Команды:"
echo "  Запуск:      systemctl start cmsdash"
echo "  Остановка:   systemctl stop cmsdash"
echo "  Перезапуск:  systemctl restart cmsdash"
echo "  Логи:        journalctl -u cmsdash -f"
