#!/bin/bash
# ============================================
# Django Auto Deployment Script
# CREATIVE COACHING AND COMPUTER CLASSES
# by ChatGPT (GPT-5)
# ============================================

# ---- CONFIGURATION ----
PROJECT_NAME="atom_orbit_project_v2"
PROJECT_DIR="/var/www/$PROJECT_NAME"
DOMAIN_NAME="atomorbit.in"
DJANGO_SETTINGS_MODULE="atom_orbit.settings"
USER="root"

# ---- 1. System Update ----
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# ---- 2. Install Dependencies ----
echo "📦 Installing dependencies..."
sudo apt install python3 python3-pip python3-venv nginx git ufw certbot python3-certbot-nginx unzip -y

# ---- 3. Setup Firewall ----
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# ---- 4. Deploy Project ----
echo "📂 Setting up project directory..."
sudo mkdir -p $PROJECT_DIR
sudo cp -r ./* $PROJECT_DIR
cd $PROJECT_DIR

# ---- 5. Python Virtual Environment ----
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# ---- 6. Install Requirements ----
echo "📦 Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt gunicorn

# ---- 7. Django Setup ----
echo "⚙️ Running Django setup..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# ---- 8. Gunicorn Service ----
echo "🧠 Configuring Gunicorn service..."
SERVICE_FILE="/etc/systemd/system/$PROJECT_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Gunicorn service for $PROJECT_NAME
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock atom_orbit.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $PROJECT_NAME
sudo systemctl start $PROJECT_NAME

# ---- 9. Nginx Setup ----
echo "🌐 Configuring Nginx..."
NGINX_FILE="/etc/nginx/sites-available/$PROJECT_NAME"

sudo bash -c "cat > $NGINX_FILE" <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root $PROJECT_DIR;
    }

    location /media/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/$PROJECT_NAME.sock;
    }
}
EOF

sudo ln -s $NGINX_FILE /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# ---- 10. SSL Setup ----
echo "🔒 Setting up SSL with Certbot..."
sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos -m admin@$DOMAIN_NAME

# ---- 11. Enable Auto-Start ----
sudo systemctl enable nginx
sudo systemctl enable $PROJECT_NAME

echo "✅ Deployment complete!"
echo "🌍 Visit: https://$DOMAIN_NAME"
