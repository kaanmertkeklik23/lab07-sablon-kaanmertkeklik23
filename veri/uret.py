#!/usr/bin/env python3
"""Kişiye özel veri üreteci — Föy 07 (FıratFit iki dünyada: SQL + NoSQL)

Kullanım:
    python3 veri/uret.py <ogrenci_no>

İki çıktı üretir:
  * Altı CSV — bilinen ilişkisel şema için (sql/sema_hazir.sql ile yüklenir)
  * veri/mongo_hazir.js — AYNI verinin doküman modeli: üç farklı modelleme
    stilini bir arada gösterir (gömülü dizi, gömülü alt doküman, referans)

Aynı öğrenci numarası her zaman aynı veriyi üretir.
"""
import csv
import json
import random
import sys
from pathlib import Path

ADLAR = ["Ahmet", "Ayşe", "Mehmet", "Elif", "Mustafa", "Zeynep", "Ali",
         "Fatma", "Hasan", "Emine", "Murat", "Hülya", "Kemal", "Nazlı",
         "Selim", "Leyla", "Orhan", "Sevgi", "Yakup", "Melek", "Deniz",
         "Ece", "Burak", "Ceren", "Tolga", "İpek", "Serkan", "Gül"]

SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Aydın",
            "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç", "Kurt",
            "Özdemir", "Erdoğan", "Polat", "Güneş", "Taş", "Bulut"]

BRANSLAR = ["Fitness", "Yoga", "Pilates", "Yüzme", "Boks", "Crossfit"]

DERS_TEMEL = ["Sabah Yogası", "Fonksiyonel Antrenman", "Yüzme Teknikleri",
              "Pilates Matwork", "Boks Temelleri", "Crossfit WOD",
              "Core Güçlendirme", "Esneklik ve Denge", "Kardiyo Dayanıklılık",
              "Kuvvet Antrenmanı", "Hamile Yogası", "Kıdemli Fitness",
              "Gençlik Yüzme", "İleri Pilates", "Kickboks"]

SEVIYELER = ["Başlangıç", "Orta", "İleri"]

SALON_ADLARI = ["Ana Salon", "Stüdyo A", "Stüdyo B", "Havuz",
                "Dövüş Salonu", "Açık Alan", "Spinning Odası"]

UCRETLER = [300, 350, 400, 450, 500, 550, 600]


def uret(ogrno: str):
    """Öğrenci numarasından deterministik altı tablo üretir."""
    tohum = int(ogrno)
    rnd = random.Random(tohum)

    salon_sayisi = 5 + tohum % 3
    salonlar = [{"salon_id": i + 1, "ad": SALON_ADLARI[i],
                 "kapasite": rnd.choice([15, 20, 25, 30, 40])}
                for i in range(salon_sayisi)]

    egitmen_sayisi = 8 + tohum % 5
    branslar = BRANSLAR[:]
    rnd.shuffle(branslar)
    egitmen_adlari = set()
    egitmenler = []
    for eid in range(1, egitmen_sayisi + 1):
        while True:
            ad = f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}"
            if ad not in egitmen_adlari:
                egitmen_adlari.add(ad)
                break
        brans = branslar[eid - 1] if eid <= 6 else rnd.choice(BRANSLAR)
        egitmenler.append({"egitmen_id": eid, "ad": ad, "brans": brans})

    ders_sayisi = 24 + tohum % 9
    ders_adlari = set()
    dersler = []
    for did in range(1, ders_sayisi + 1):
        while True:
            ad = f"{rnd.choice(DERS_TEMEL)} — {rnd.choice(SEVIYELER)}"
            if ad not in ders_adlari:
                ders_adlari.add(ad)
                break
        dersler.append({
            "ders_id": did,
            "ad": ad,
            "egitmen_id": rnd.randint(1, egitmen_sayisi),
            "salon_id": rnd.randint(1, salon_sayisi),
            "ucret": rnd.choice(UCRETLER),
        })

    uye_sayisi = 150 + tohum % 51
    uyeler = []
    telefonlar = []
    tel_id = 0
    for uid in range(1, uye_sayisi + 1):
        uyeler.append({
            "uye_id": uid,
            "ad": f"{rnd.choice(ADLAR)} {rnd.choice(SOYADLAR)}",
            "dogum_yili": rnd.randint(1965, 2008),
        })
        for _ in range(rnd.randint(1, 3)):
            tel_id += 1
            telefonlar.append({
                "telefon_id": tel_id,
                "uye_id": uid,
                "numara": f"05{rnd.randint(30, 55)}-{rnd.randint(100, 999)}-"
                          f"{rnd.randint(1000, 9999)}",
            })

    # Föy 07 deneyleri üye 10 ve 20'yi hedefler: ikisi de kayıtlı kalsın.
    kayitsiz_sayisi = 3 + tohum % 4
    kayitsizlar = set(rnd.sample(range(21, uye_sayisi + 1), kayitsiz_sayisi))
    kayit_uyeleri = [u for u in range(1, uye_sayisi + 1) if u not in kayitsizlar]

    kayit_hedefi = 320 + tohum % 101
    ikili_kume = set()
    kayitlar = []
    kid = 0
    while kid < kayit_hedefi:
        uye = rnd.choice(kayit_uyeleri)
        ders = rnd.randint(1, ders_sayisi)
        if (uye, ders) in ikili_kume:
            continue
        ikili_kume.add((uye, ders))
        kid += 1
        ay = kid if kid <= 12 else rnd.randint(1, 12)
        gun = rnd.randint(1, 28)
        kayitlar.append({
            "kayit_id": kid,
            "uye_id": uye,
            "ders_id": ders,
            "tarih": f"2026-{ay:02d}-{gun:02d}",
        })

    # Üye 20'nin en az bir kaydı olsun (öksüz kayıt deneyi için).
    if not any(k["uye_id"] == 20 for k in kayitlar):
        kayitlar[12]["uye_id"] = 20

    return {"uyeler": uyeler, "telefonlar": telefonlar,
            "egitmenler": egitmenler, "salonlar": salonlar,
            "dersler": dersler, "kayitlar": kayitlar}


def mongo_js(t):
    """Aynı verinin doküman modeli — üç stil bir arada:
    uyeler: telefonlar GÖMÜLÜ DİZİ; dersler: egitmen/salon GÖMÜLÜ ALT
    DOKÜMAN; kayitlar: uye_id/ders_id REFERANS."""
    tel_map = {}
    for tel in t["telefonlar"]:
        tel_map.setdefault(tel["uye_id"], []).append(tel["numara"])
    egitmen = {e["egitmen_id"]: e for e in t["egitmenler"]}
    salon = {s["salon_id"]: s for s in t["salonlar"]}

    uyeler = [{"_id": u["uye_id"], "ad": u["ad"],
               "dogum_yili": u["dogum_yili"],
               "telefonlar": tel_map.get(u["uye_id"], [])}
              for u in t["uyeler"]]
    dersler = [{"_id": d["ders_id"], "ad": d["ad"], "ucret": d["ucret"],
                "egitmen": {"ad": egitmen[d["egitmen_id"]]["ad"],
                            "brans": egitmen[d["egitmen_id"]]["brans"]},
                "salon": {"ad": salon[d["salon_id"]]["ad"],
                          "kapasite": salon[d["salon_id"]]["kapasite"]}}
               for d in t["dersler"]]
    kayitlar = [{"_id": k["kayit_id"], "uye_id": k["uye_id"],
                 "ders_id": k["ders_id"], "tarih": k["tarih"]}
                for k in t["kayitlar"]]

    def js(x):
        return json.dumps(x, ensure_ascii=False)

    return (
        "// Föy 07 — doküman modeli kurulumu (uret.py tarafından üretildi)\n"
        "// Çalıştırma: docker exec -i vtys-mongo mongosh --quiet vtysdb < veri/mongo_hazir.js\n"
        "db = db.getSiblingDB('vtysdb');\n"
        "db.uyeler.drop(); db.dersler.drop(); db.kayitlar.drop();\n"
        f"db.uyeler.insertMany({js(uyeler)});\n"
        f"db.dersler.insertMany({js(dersler)});\n"
        f"db.kayitlar.insertMany({js(kayitlar)});\n"
        "print('uyeler:', db.uyeler.countDocuments());\n"
        "print('dersler:', db.dersler.countDocuments());\n"
        "print('kayitlar:', db.kayitlar.countDocuments());\n"
    )


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Kullanım: python3 veri/uret.py <ogrenci_no>")
        print("Örnek   : python3 veri/uret.py 230541001")
        sys.exit(1)

    ogrno = sys.argv[1]
    klasor = Path(__file__).resolve().parent
    t = uret(ogrno)

    for ad, satirlar in t.items():
        hedef = klasor / f"{ad}.csv"
        with open(hedef, "w", newline="", encoding="utf-8") as f:
            yazici = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
            yazici.writeheader()
            yazici.writerows(satirlar)
        print(f"Üretildi: {hedef.name:16s} ({len(satirlar)} satır)")

    mongo_hedef = klasor / "mongo_hazir.js"
    mongo_hedef.write_text(mongo_js(t), encoding="utf-8")
    print(f"Üretildi: {mongo_hedef.name} (doküman modeli)")
    print("Bu veriler size özeldir; sonuçlarınız sınıftaki herkesten farklıdır.")


if __name__ == "__main__":
    main()
