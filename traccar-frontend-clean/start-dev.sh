#!/bin/bash

# Traccar Frontend Clean - Development Startup Script
# Este script inicia o frontend limpo na porta 3002 apontando para a API Python

echo "🚀 Iniciando Traccar Frontend Clean..."
echo "📡 API Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3005"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências..."
    npm install
    echo ""
fi

# Verificar se a API está rodando
echo "🔍 Verificando se a API Python está rodando na porta 8000..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API Python está rodando na porta 8000"
    echo "   Status: $(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo 'healthy')"
else
    echo "⚠️  API Python não está rodando na porta 8000"
    echo "   Para iniciar a API:"
    echo "   cd ../traccar-python-api && uvicorn app.main:app --reload"
    echo ""
fi

echo "🎯 Iniciando servidor de desenvolvimento..."
echo "   Frontend estará disponível em: http://localhost:3005"
echo "   Proxy configurado para: http://localhost:8000"
echo ""

# Iniciar o servidor de desenvolvimento
npm run start

