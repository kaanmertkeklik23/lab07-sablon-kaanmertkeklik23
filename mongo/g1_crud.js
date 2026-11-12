// =====================================================
// Föy 07 / Görev 1 — CRUD işlemleri
// Bu dosya mongosh ile çalıştırılabilir olmalı:
//   docker exec -i vtys-mongo mongosh --quiet vtysdb < mongo/g1_crud.js
// Föydeki dört işlemi sırasıyla yazın:
//   1) insertOne: _id 9001 ile kendinizi üye yapın (telefonlar dizisiyle)
//   2) updateOne: 10 numaralı üyenin dogum_yili → 1999
//   3) deleteOne: 20 numaralı üyeyi silin
//   4) countDocuments: üye 20'nin ÖKSÜZ kalan kayıtlarını sayın
//      (çıktıyı sonuc/g1.txt dosyasına da yazın)
// =====================================================
db = db.getSiblingDB('vtysdb');

db.uyeler.insertOne({
  _id: 9001,
  ad: "Kaan Mert KEKLİK",
  dogum_yili: 2004,
  telefonlar: ["0532-123-4567"]
});

db.uyeler.updateOne(
  { _id: 10 },
  { $set: { dogum_yili: 1999 } }
);

db.uyeler.deleteOne({ _id: 20 });

print(db.kayitlar.countDocuments({ uye_id: 20 }));
