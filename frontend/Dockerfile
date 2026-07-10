# Immagine pinnata per digest (mai "latest"). Node 22 LTS alpine.
FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2

WORKDIR /app

# L'immagine node include già l'utente non-root "node": gli assegno la workdir.
RUN chown node:node /app
USER node

# Cache dei moduli: si reinstalla solo se cambiano i manifest.
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .

EXPOSE 5173

# Dev server in ascolto su tutte le interfacce (raggiungibile dall'host).
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
