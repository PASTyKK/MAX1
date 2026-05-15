FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY mobile.html /usr/share/nginx/html/mobile.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]