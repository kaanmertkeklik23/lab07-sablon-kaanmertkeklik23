# Föy 07 — NoSQL: MongoDB ve Redis

Modern Veritabanı Yönetim Sistemleri — Laboratuvar teslim deposu.
Görevlerin tam açıklaması **Föy 07 PDF**'indedir; bu dosya kısa bir hatırlatmadır.

## Bu hafta

Aynı FıratFit verisi **iki dünyada**: bildiğiniz ilişkisel şema (PostgreSQL)
ve doküman modeli (MongoDB). Doküman modeli üç stili bir arada gösterir:
telefonlar **gömülü dizi**, ders içinde eğitmen/salon **gömülü alt doküman**,
kayıtlar **referans**. Ayrıca Redis ile anahtar-değer/önbellek dünyasına
ilk adımı atacaksınız.

## Hızlı başlangıç

```bash
echo "230541001" > ogrno.txt              # kendi numaranız
docker compose up -d                       # postgres + mongo + redis
python3 veri/uret.py 230541001            # kendi numaranız

# SQL dünyası (karşılaştırma görevleri için):
docker exec -i vtys-postgres psql -U vtys -d vtysdb < sql/sema_hazir.sql

# Doküman dünyası:
docker exec -i vtys-mongo mongosh --quiet vtysdb < veri/mongo_hazir.js
docker exec -it vtys-mongo mongosh vtysdb      # etkileşimli kabuk

# Anahtar-değer dünyası:
docker exec -it vtys-redis redis-cli
```

## Depo yapısı

| Yol | Ne |
|---|---|
| `ogrno.txt` | Öğrenci numaranız (ilk iş: doldurun) |
| `veri/mongo_hazir.js` | Doküman modeli kurulumu (uret.py üretir) |
| `sql/sema_hazir.sql` | İlişkisel taraf — HAZIR |
| `mongo/g1_crud.js` | Görev 1 — CRUD işlemleriniz |
| `mongo/g2_sorgular.js` | Görev 2 — doküman sorgularınız |
| `sonuc/` | Transkriptler, karşılaştırma raporu, AI köşesi |

Değerlendirici, CRUD betiğinizi CI'daki MongoDB'de çalıştırıp sonucu
veritabanı **durumundan** doğrular; transkriptlerdeki sayılar size özeldir.


## Push etmeden önce kendinizi kontrol edin

Değerlendiriciyi kendi bilgisayarınızda çalıştırabilirsiniz — GitHub'daki ile
**aynı dosya, aynı puan**:

```bash
docker compose run --rm kontrol
```

Ekrana görev görev puanınız ve eksikleriniz düşer. İlk çalıştırma birkaç
saniye sürer, sonrakiler ~2 saniye. Ayrıca bir şey kurmanız gerekmez; Docker
zaten kurulu.

**Önce burada tam puan alın, sonra push edin.** Her push GitHub'da sınıfın
ortak Actions kotasından dakika harcar; deneme-yanılmayı buraya taşırsanız
kota dönem sonuna kadar yeter.

## Teslim

```bash
git add ogrno.txt mongo/ sonuc/
git commit -m "Foy 07 teslimi"
git push
```
