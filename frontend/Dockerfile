# Etapa 1: Compilacion y empaquetado de React con Vite
FROM node:20-alpine AS compilador

# Directorio de trabajo
WORKDIR /app

# Copia de definicion de paquetes para aprovechar la cache de Docker
COPY package*.json ./
RUN npm install

# Copia del codigo fuente y compilacion para produccion usando el proxy /api de Nginx
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
COPY . .
RUN npm run build

# Etapa 2: Servidor web de produccion Nginx ligero
FROM nginx:alpine

# Copia de los archivos compilados en la etapa previa
COPY --from=compilador /app/dist /usr/share/nginx/html

# Copia de la configuracion personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Puerto expuesto para navegacion web
EXPOSE 80

# Ejecucion de Nginx en primer plano
CMD ["nginx", "-g", "daemon off;"]
