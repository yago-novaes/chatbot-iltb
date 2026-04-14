#!/usr/bin/env bash
# =============================================================================
# setup-vps.sh — Provisionamento da CX22 (Ubuntu 22.04) para chatbot ILTB
# =============================================================================
# Uso:
#   1. Copiar este script para a VPS:
#        scp infra/setup-vps.sh root@<IP>:/root/
#   2. Executar como root:
#        ssh root@<IP> "bash /root/setup-vps.sh <DOMINIO> <EMAIL_CERTBOT>"
#
#   Exemplo:
#        bash setup-vps.sh chatbot.iltb.exemplo.com.br admin@exemplo.com.br
#
# O script é idempotente — pode ser reexecutado sem efeitos colaterais.
# =============================================================================
set -euo pipefail

DOMAIN="${1:?Informe o domínio. Ex: bash setup-vps.sh chatbot.exemplo.com EMAIL}"
EMAIL="${2:?Informe o e-mail para o Certbot. Ex: bash setup-vps.sh DOMINIO admin@exemplo.com}"
APP_DIR="/opt/iltb-chatbot"
APP_USER="iltb"

echo ""
echo "======================================"
echo "  Setup VPS — Chatbot ILTB"
echo "  Domínio : $DOMAIN"
echo "  E-mail  : $EMAIL"
echo "  Diretório: $APP_DIR"
echo "======================================"
echo ""

# ------------------------------------------------------------------------------
# 1. Atualizar sistema
# ------------------------------------------------------------------------------
echo "[1/8] Atualizando pacotes do sistema..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl git ufw nginx certbot python3-certbot-nginx

# ------------------------------------------------------------------------------
# 2. Instalar Docker Engine (não Docker Desktop)
# ------------------------------------------------------------------------------
echo "[2/8] Instalando Docker Engine..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "  Docker já instalado ($(docker --version)). Pulando."
fi

# docker compose plugin (v2)
if ! docker compose version &>/dev/null 2>&1; then
    apt-get install -y -qq docker-compose-plugin
fi

# ------------------------------------------------------------------------------
# 3. Criar usuário não-root para a aplicação
# ------------------------------------------------------------------------------
echo "[3/8] Criando usuário '$APP_USER'..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    usermod -aG docker "$APP_USER"
    echo "  Usuário '$APP_USER' criado e adicionado ao grupo docker."
else
    echo "  Usuário '$APP_USER' já existe. Pulando."
fi

# ------------------------------------------------------------------------------
# 4. Firewall UFW
# ------------------------------------------------------------------------------
echo "[4/8] Configurando UFW..."
# Nota: Docker ignora UFW via iptables direto.
# A porta 8000 está vinculada em 127.0.0.1 no docker-compose.yml,
# então nunca fica exposta externamente — UFW é uma camada extra de defesa.
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment "SSH"
ufw allow 80/tcp   comment "HTTP (redirect para HTTPS)"
ufw allow 443/tcp  comment "HTTPS"
ufw --force enable
echo "  UFW ativado. Regras:"
ufw status verbose

# ------------------------------------------------------------------------------
# 5. Clonar repositório
# ------------------------------------------------------------------------------
echo "[5/8] Configurando diretório da aplicação em $APP_DIR..."
if [ ! -d "$APP_DIR/.git" ]; then
    echo "  ATENÇÃO: clone o repositório manualmente antes de continuar:"
    echo ""
    echo "    git clone <URL_DO_REPO> $APP_DIR"
    echo "    chown -R $APP_USER:$APP_USER $APP_DIR"
    echo ""
    echo "  Depois execute: bash $APP_DIR/infra/setup-vps.sh $DOMAIN $EMAIL"
    echo ""
    # Cria o diretório para o próximo passo não falhar
    mkdir -p "$APP_DIR"
else
    echo "  Repositório já clonado. Atualizando..."
    git -C "$APP_DIR" pull --ff-only
fi

# ------------------------------------------------------------------------------
# 6. Configurar Nginx
# ------------------------------------------------------------------------------
echo "[6/8] Configurando Nginx..."
NGINX_CONF="/etc/nginx/sites-available/iltb-chatbot"

# Substitui o placeholder DOMINIO_PLACEHOLDER pelo domínio real
sed "s/DOMINIO_PLACEHOLDER/$DOMAIN/g" \
    "$APP_DIR/infra/nginx/default.conf" > "$NGINX_CONF"

# Ativa o site
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/iltb-chatbot
# Remove o site default do Nginx para não conflitar
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
echo "  Nginx configurado para $DOMAIN."

# Diretório para desafio ACME (certbot standalone)
mkdir -p /var/www/certbot

# ------------------------------------------------------------------------------
# 7. Obter certificado TLS com Certbot
# ------------------------------------------------------------------------------
echo "[7/8] Obtendo certificado TLS para $DOMAIN..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    certbot --nginx \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --domains "$DOMAIN" \
        --redirect
    echo "  Certificado obtido com sucesso."
else
    echo "  Certificado já existe. Verificando renovação..."
    certbot renew --dry-run
fi

# Cron de renovação automática (certbot já instala por padrão no Ubuntu 22.04,
# mas garantimos aqui)
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | crontab -
    echo "  Cron de renovação do certificado configurado (03:00 diário)."
fi

# ------------------------------------------------------------------------------
# 8. Arquivo .env de produção
# ------------------------------------------------------------------------------
echo "[8/8] Verificando .env de produção..."
ENV_FILE="$APP_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$APP_DIR/infra/.env.production" "$ENV_FILE"
    echo ""
    echo "  ATENÇÃO: preencha $ENV_FILE com as chaves reais antes de subir a aplicação:"
    echo ""
    echo "    nano $ENV_FILE"
    echo ""
else
    echo "  .env já existe. Não sobrescrito."
fi

# Permissões restritas no .env (chaves de API)
chmod 600 "$ENV_FILE" 2>/dev/null || true
chown "$APP_USER:$APP_USER" "$ENV_FILE" 2>/dev/null || true

# ------------------------------------------------------------------------------
# Resumo final
# ------------------------------------------------------------------------------
echo ""
echo "======================================"
echo "  Provisionamento concluído!"
echo "======================================"
echo ""
echo "  Próximos passos:"
echo ""
echo "  1. Se o repositório ainda não foi clonado:"
echo "       git clone <URL> $APP_DIR"
echo "       chown -R $APP_USER:$APP_USER $APP_DIR"
echo ""
echo "  2. Preencher as chaves no .env:"
echo "       nano $APP_DIR/.env"
echo ""
echo "  3. Subir a aplicação:"
echo "       cd $APP_DIR && docker compose -f infra/docker-compose.yml up -d"
echo ""
echo "  4. Indexar os documentos:"
echo "       docker compose -f infra/docker-compose.yml exec app python -m app.scripts.ingest"
echo ""
echo "  5. Verificar:"
echo "       curl https://$DOMAIN/health"
echo ""
