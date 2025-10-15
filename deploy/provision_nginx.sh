#!/usr/bin/env bash
set -euo pipefail

# provision_nginx.sh
# Usage: sudo ./deploy/provision_nginx.sh example.com /srv/aldudu-academy
# This script installs nginx + certbot (Debian/Ubuntu), deploys a site config, enables it, opens firewall, and obtains TLS cert.

DOMAIN=${1:-}
APP_DIR=${2:-/srv/aldudu-academy}
NGINX_SITE_NAME=${3:-aldudu}

if [ -z "$DOMAIN" ]; then
  echo "Usage: sudo $0 <your-domain> [app-dir] [site-name]"
  exit 2
fi

echo "Domain: $DOMAIN"
echo "App dir: $APP_DIR"

# Install nginx and certbot
if ! command -v nginx >/dev/null 2>&1; then
  echo "Installing nginx and certbot..."
  apt-get update
  apt-get install -y nginx certbot python3-certbot-nginx
fi

# Create directories
if [ ! -d "$APP_DIR" ]; then
  echo "App directory $APP_DIR does not exist. Please clone repo to that path and ensure static files are at $APP_DIR/static"
  exit 3
fi

# Prepare site config from deploy/nginx.conf (template)
TEMPLATE="$PWD/deploy/nginx.conf"
if [ ! -f "$TEMPLATE" ]; then
  echo "Template $TEMPLATE not found in repo."
  exit 4
fi

SITES_AVAILABLE="/etc/nginx/sites-available"
SITES_ENABLED="/etc/nginx/sites-enabled"
SITE_CONF="$SITES_AVAILABLE/$NGINX_SITE_NAME"

# Replace placeholder server_name and static path in the template
sed \
  -e "s/server_name example.com;/server_name $DOMAIN;/g" \
  -e "s|alias /srv/aldudu-academy/static/;|alias $APP_DIR/static/;|g" \
  "$TEMPLATE" > "$SITE_CONF"

# Enable site
ln -sf "$SITE_CONF" "$SITES_ENABLED/$NGINX_SITE_NAME"

# Test nginx config and reload
nginx -t
systemctl reload nginx

# Open firewall for Nginx Full if ufw present
if command -v ufw >/dev/null 2>&1; then
  echo "Configuring UFW to allow Nginx Full..."
  ufw allow 'Nginx Full'
fi

# Obtain TLS certificate via certbot nginx plugin
echo "Requesting TLS certificate via certbot for $DOMAIN"
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN" || {
  echo "Certbot failed. Check /var/log/letsencrypt for details."
}

# Optional: restart nginx
systemctl reload nginx

echo "Done. Nginx configured for $DOMAIN."
