#!/bin/bash
echo "🚀 Iniciando Ciclo de Atualização Consultoc..."

# 1. Puxar novidades do GitHub
git pull origin main

# 2. Reiniciar o motor da API (Docker)
echo "🐳 Atualizando o container..."
docker stop consultoc-app || true
docker rm -f consultoc-app || true
docker build -t consultoc-api .
docker run -d -p 8000:8000 --env-file .env --name consultoc-app consultoc-api

# 3. Sincronizar Ficheiros Visuais (Frontend)
echo "🌐 Sincronizando interface..."
# Este comando garante que os HTMLs na pasta atual sejam movidos para o servidor
sudo cp form.html /var/www/consultoc-frontend/ || true
sudo cp dashboard.html /var/www/consultoc-frontend/ || true
sudo chmod 644 /var/www/consultoc-frontend/*.html

# 4. Reiniciar o Porteiro (Nginx)
echo "🛡️ Reiniciando Nginx..."
sudo systemctl restart nginx

echo "✅ Atualização concluída com sucesso!"