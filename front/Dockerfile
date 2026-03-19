# Étape 1 : Construction (Build)
FROM node:20-alpine AS builder

WORKDIR /app

# Copier les fichiers de dépendances
COPY package.json package-lock.json ./
RUN npm install

# Copier le reste du code source
COPY . .

# Construire l'application Vite (génère un dossier 'dist')
RUN npm run build

# Étape 2 : Serveur web (Nginx)
FROM nginx:alpine

# Copier l'application construite depuis l'étape 1 vers le dossier public Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Exposer le port HTTP
EXPOSE 80

# Copier la configuration Nginx pour SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
