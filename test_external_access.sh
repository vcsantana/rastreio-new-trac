#!/bin/bash

# Script de teste para acesso externo ao Traccar
# Testa conectividade via 5G e rede local

echo "🔍 Testando Acesso Externo ao Traccar"
echo "======================================"

# Configurações
NOIP_DOMAIN="qvnk.no-ip.org"
PORT="5055"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "📋 Configurações:"
echo "   Domínio no-ip: $NOIP_DOMAIN"
echo "   Porta: $PORT"
echo "   IP Local: $LOCAL_IP"
echo ""

# Teste 1: Verificar se o servidor está rodando localmente
echo "1️⃣ Testando servidor local..."
if curl -s --connect-timeout 5 http://localhost:$PORT > /dev/null; then
    echo "   ✅ Servidor local funcionando"
else
    echo "   ❌ Servidor local não está respondendo"
    exit 1
fi

# Teste 2: Verificar resolução DNS
echo ""
echo "2️⃣ Testando resolução DNS..."
DNS_IP=$(nslookup $NOIP_DOMAIN | grep "Address:" | tail -1 | awk '{print $2}')
if [ ! -z "$DNS_IP" ]; then
    echo "   ✅ DNS resolvido: $NOIP_DOMAIN -> $DNS_IP"
else
    echo "   ❌ Falha na resolução DNS"
    exit 1
fi

# Teste 3: Verificar se a porta está aberta no servidor
echo ""
echo "3️⃣ Testando porta no servidor..."
if netstat -an | grep "\.$PORT.*LISTEN" > /dev/null; then
    echo "   ✅ Porta $PORT está escutando"
else
    echo "   ❌ Porta $PORT não está escutando"
    exit 1
fi

# Teste 4: Testar conectividade externa
echo ""
echo "4️⃣ Testando conectividade externa..."
if timeout 10 bash -c "</dev/tcp/$NOIP_DOMAIN/$PORT" 2>/dev/null; then
    echo "   ✅ Porta $PORT acessível externamente"
else
    echo "   ❌ Porta $PORT não acessível externamente"
    echo "   🔧 Possíveis soluções:"
    echo "      - Verificar firewall do servidor"
    echo "      - Configurar port forwarding no roteador"
    echo "      - Verificar se ISP não bloqueia a porta"
fi

# Teste 5: Testar via IP local
echo ""
echo "5️⃣ Testando via IP local..."
if curl -s --connect-timeout 5 http://$LOCAL_IP:$PORT > /dev/null; then
    echo "   ✅ Acessível via IP local: $LOCAL_IP:$PORT"
else
    echo "   ❌ Não acessível via IP local"
fi

echo ""
echo "📱 Configurações para o App OsmAnd:"
echo "   URL Local: http://$LOCAL_IP:$PORT"
echo "   URL Externa: http://$NOIP_DOMAIN:$PORT"
echo ""
echo "🔧 Se não funcionar via 5G:"
echo "   1. Verificar port forwarding no roteador"
echo "   2. Liberar porta $PORT no firewall"
echo "   3. Testar com porta alternativa (8080, 8081, etc.)"
echo "   4. Verificar se ISP bloqueia a porta"
