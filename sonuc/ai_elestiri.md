Araç: ChatGPT, 13.11.2026

İstem (Prompt):
Föy 04'teki eğitmen başına toplam kayıt sayısını bulan SQL sorgumuz şöyleydi:
```sql
SELECT e.ad, COUNT(k.kayit_id) AS toplam_kayit
FROM egitmenler e
JOIN dersler d ON d.egitmen_id = e.egitmen_id
JOIN kayitlar k ON k.ders_id = d.ders_id
GROUP BY e.egitmen_id, e.ad
ORDER BY toplam_kayit DESC;
```
Biz bu hafta aynı veriyi MongoDB'ye taşıdık. `dersler` koleksiyonunda eğitmen ve salon bilgileri alt doküman olarak gömülü duruyor (`egitmen: { ad, brans }`), `kayitlar` koleksiyonunda ise `uye_id` ve `ders_id` referans olarak tutuluyor. Bu SQL sorgusunu bizim MongoDB yapımıza göre aggregate sorgusuna çevirir misin?

Modelin Ürettiği Sorgu:
```javascript
db.dersler.aggregate([
  {
    $lookup: {
      from: "egitmenler",
      localField: "egitmen_id",
      foreignField: "_id",
      as: "egitmen_bilgi"
    }
  },
  {
    $lookup: {
      from: "kayitlar",
      localField: "_id",
      foreignField: "ders_id",
      as: "ders_kayitlari"
    }
  },
  { $unwind: "$ders_kayitlari" },
  {
    $group: {
      _id: "$egitmen.ad",
      toplam_kayit: { $sum: 1 }
    }
  },
  { $sort: { toplam_kayit: -1 } }
])
```

Mongosh Çıktısı:
```javascript
[
  { _id: 'Zeynep Erdoğan', toplam_kayit: 67 },
  { _id: 'Orhan Çetin', toplam_kayit: 65 },
  { _id: 'Ece Erdoğan', toplam_kayit: 60 },
  { _id: 'İpek Demir', toplam_kayit: 45 },
  { _id: 'Sevgi Çetin', toplam_kayit: 39 },
  { _id: 'Tolga Polat', toplam_kayit: 34 },
  { _id: 'Burak Çetin', toplam_kayit: 31 },
  { _id: 'Zeynep Kurt', toplam_kayit: 28 }
]
```

Değerlendirmem:
ChatGPT'ye istemde eğitmen bilgisinin `dersler` içine gömülü olduğunu söylememe rağmen SQL'deki 3 tablolu JOIN mantığından çıkamayıp iki tane `$lookup` yazdı. İlk `$lookup` adımında sanki ayrı bir `egitmenler` koleksiyonu varmış gibi birleştirme yapmaya çalışmış ama bizim MongoDB veritabanımızda öyle bir koleksiyon zaten yok. İşin ilginç yanı, alttaki `$group` kısmında `_id: "$egitmen.ad"` kullandığı için sorgu hata vermeden çalıştı ve PostgreSQL ile birebir aynı sayıları (Zeynep Erdoğan 67, Orhan Çetin 65, Ece Erdoğan 60 vb.) döndürdü; yani yazdığı ilk `$lookup` tamamen boşa çalışmış oldu. Ayrıca `dersler` tablosundan başlayıp kayıtları dizi olarak çekip sonra `$unwind` ile tekrar tek tek açması da gereksiz uzatmış. Halbuki doğrudan `kayitlar` koleksiyonundan başlayıp `dersler`e tek bir `$lookup` atmak ve gömülü olan `ders.egitmen.ad` alanına göre gruplamak çok daha temiz ve doğru oluyor.

Sadeleştirilmiş Hali:
```javascript
db.kayitlar.aggregate([
  {
    $lookup: {
      from: "dersler",
      localField: "ders_id",
      foreignField: "_id",
      as: "ders"
    }
  },
  { $unwind: "$ders" },
  {
    $group: {
      _id: "$ders.egitmen.ad",
      toplam_kayit: { $sum: 1 }
    }
  },
  { $sort: { toplam_kayit: -1 } }
])
```
