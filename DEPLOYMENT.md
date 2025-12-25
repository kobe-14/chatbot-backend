# 🚀 Deployment Guide

## 📋 Overview

This guide covers deploying the Harish Chatbot to production using Docker.

---

## 🔒 Production vs Development

### **Production** (Recommended for Server)
- ✅ Uses **named volumes** (managed by Docker)
- ✅ Better performance and portability
- ✅ Automatic backups possible
- ✅ Data persists across container recreations
- ⚠️ Less direct access to database file

### **Development** (Local Testing)
- ✅ Uses **bind mounts** (direct file access)
- ✅ Easy to inspect `agno.db` directly
- ✅ Can edit code and see changes
- ⚠️ Platform-specific paths

---

## 🛠️ Deployment Options

### **Option 1: Production Deployment (Named Volumes)**

#### 1. On Your Server, clone/upload the project:
```bash
cd /var/www/
git clone <your-repo> harish-chatbot
cd harish-chatbot
```

#### 2. Create `.env` file:
```bash
nano .env
```

Add your credentials:
```env
OPENAI_API_KEY=sk-your-key-here
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here
```

#### 3. Build and run:
```bash
docker-compose up -d --build
```

#### 4. Check status:
```bash
docker-compose ps
docker-compose logs -f chatbot
```

#### 5. Access your chatbot:
```
http://your-server-ip:8000
http://your-server-ip:8000/docs  # API documentation
```

---

### **Option 2: Development Deployment (Bind Mounts)**

For local development/testing:

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

---

## 🗂️ Volume Management (Production)

### **List volumes:**
```bash
docker volume ls
```

### **Inspect volume:**
```bash
docker volume inspect agents_chatbot-data
```

### **Backup database:**
```bash
# Create backup directory
mkdir -p backups

# Copy database from volume
docker run --rm \
  -v agents_chatbot-data:/data \
  -v $(pwd)/backups:/backup \
  alpine cp /data/agno.db /backup/agno-$(date +%Y%m%d-%H%M%S).db
```

### **Restore database:**
```bash
docker run --rm \
  -v agents_chatbot-data:/data \
  -v $(pwd)/backups:/backup \
  alpine cp /backup/agno-20241223.db /data/agno.db
```

### **Access database directly:**
```bash
docker run --rm -it \
  -v agents_chatbot-data:/data \
  alpine sh

# Inside container:
cd /data
ls -la
```

---

## 🌐 Nginx Reverse Proxy (Recommended)

### **Why?**
- Use domain name instead of IP:port
- SSL/HTTPS support
- Better security

### **Setup:**

1. Install Nginx on server:
```bash
sudo apt update
sudo apt install nginx
```

2. Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/chatbot
```

Add:
```nginx
server {
    listen 80;
    server_name chatbot.yourwebsite.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. Add SSL with Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d chatbot.yourwebsite.com
```

Now access via: `https://chatbot.yourwebsite.com`

---

## 🔧 Common Commands

### **Start:**
```bash
docker-compose up -d
```

### **Stop:**
```bash
docker-compose down
```

### **View logs:**
```bash
docker-compose logs -f chatbot
```

### **Restart:**
```bash
docker-compose restart chatbot
```

### **Update code:**
```bash
git pull
docker-compose up -d --build
```

### **Shell access:**
```bash
docker exec -it harish-chatbot sh
```

---

## 📊 Monitoring

### **Check health:**
```bash
curl http://localhost:8000/health
```

### **Check resources:**
```bash
docker stats harish-chatbot
```

### **Auto-restart on failure:**
Already configured with `restart: unless-stopped`

---

## 🔐 Security Checklist

- ✅ Never commit `.env` file
- ✅ Use strong API keys
- ✅ Enable firewall (allow only 80, 443, SSH)
- ✅ Use Nginx reverse proxy
- ✅ Enable SSL/HTTPS
- ✅ Regular database backups
- ✅ Keep Docker images updated
- ✅ Monitor logs for suspicious activity

---

## 🆘 Troubleshooting

### **Container won't start:**
```bash
docker-compose logs chatbot
```

### **Database locked:**
Stop container, backup, restart:
```bash
docker-compose down
# Backup volume
docker-compose up -d
```

### **Port already in use:**
Change port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Use 8080 instead
```

### **Out of disk space:**
Clean up Docker:
```bash
docker system prune -a
```

---

## 📦 Production Checklist

- [ ] Created `.env` with all credentials
- [ ] Tested locally with Docker
- [ ] Set up server with Docker installed
- [ ] Configured firewall rules
- [ ] Set up Nginx reverse proxy
- [ ] Enabled SSL certificate
- [ ] Tested API endpoints
- [ ] Set up database backup cron job
- [ ] Configured monitoring/alerts
- [ ] Documented server access details

---

## 🎯 Next Steps

1. Deploy to your server
2. Set up automated backups (cron job)
3. Monitor logs and performance
4. Integrate with your website frontend
5. Set up CI/CD for automatic deployments

Happy Deploying! 🚀
