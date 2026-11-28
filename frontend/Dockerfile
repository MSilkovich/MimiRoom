FROM node:22-alpine
WORKDIR /app
COPY --chown=node:node . .
RUN mkdir -p .data && chown node:node .data
USER node
ENV SUPPORT_HOST=0.0.0.0 SUPPORT_PORT=4180 AI_ENABLED=false TELEGRAM_ENABLED=false
EXPOSE 4180
CMD ["node", "server/http.mjs"]
