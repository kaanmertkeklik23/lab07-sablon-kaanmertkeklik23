# Yerel "docker compose run --rm kontrol" icin degerlendirme ortami.
# Degerlendirici ogrencinin betiklerini mongosh ile calistirdigindan
# python imajina mongosh'u da kuruyoruz — GitHub Actions'taki adimin
# aynisi (npm install -g mongosh). Imaj bir kez kurulur; sonraki
# calistirmalarda Docker onbellekten alir, saniyeler surer.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm ca-certificates \
 && npm install -g mongosh \
 && npm cache clean --force \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pymongo
