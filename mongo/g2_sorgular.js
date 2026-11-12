// =====================================================
// Föy 07 / Görev 2 — Doküman sorguları
// Her sorguyu ilgili "// Soru 2.x" başlığının ALTINA yazın;
// çıktıları mongosh'ta çalıştırıp sonuc/g2.txt dosyasına kaydedin.
// =====================================================
db = db.getSiblingDB('vtysdb');

// Soru 2.1
// (2000 ve sonrası doğumlu üye sayısı)
db.uyeler.countDocuments({ dogum_yili: { $gte: 2000 } });

// Soru 2.2
// (Ücreti 500'den yüksek derslerin adı ve ücreti)
db.dersler.find({ ucret: { $gt: 500 } }, { ad: 1, ucret: 1, _id: 0 });

// Soru 2.3
// (Tam 3 telefonu olan üye sayısı — gömülü diziyi sorgulayın)
db.uyeler.countDocuments({ telefonlar: { $size: 3 } });

// Soru 2.4
// (aggregate + $group: her dersin kayıt sayısı, en çoktan aza ilk 5)
db.kayitlar.aggregate([
  { $group: { _id: "$ders_id", adet: { $sum: 1 } } },
  { $sort: { adet: -1 } },
  { $limit: 5 }
]);
