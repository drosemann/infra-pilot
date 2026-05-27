FROM node:18-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:18-alpine

WORKDIR /app
RUN apk add --no-cache tzdata
COPY --from=build /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=production
USER node

CMD ["node", "index.js"]
