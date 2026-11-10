#!/usr/bin/env python3
"""Föy 07 — Otomatik Değerlendirici

GitHub Actions içinde çalışır. Doküman modelini öğrencinin numarasından
üretilen KİŞİYE ÖZEL veriyle CI'daki MongoDB'ye kurar, öğrencinin CRUD ve
sorgu betiklerini mongosh ile çalıştırır ve:

  * CRUD sonuçlarını doğrudan veritabanı DURUMUNDAN doğrular (pymongo),
  * transkriptlerdeki kişiye özel sayıları kontrol eder,
  * Redis ve karşılaştırma raporlarını anahtar kanıtlar üzerinden okur.

Beklenen sayılar üreteçten Python ile hesaplanır; hazır sorgu cevabı yoktur.
"""
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "veri"))
from uret import uret, mongo_js  # noqa: E402

try:
    from pymongo import MongoClient
except ImportError:
    print("HATA: pymongo kurulu değil (pip install pymongo).")
    sys.exit(2)

SONUCLAR = []
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGOSH = os.environ.get("MONGOSH", "mongosh")


def kaydet(gorev, alinan, tam, mesaj):
    SONUCLAR.append((gorev, alinan, tam, mesaj))
    durum = "✓" if alinan == tam else ("~" if alinan > 0 else "✗")
    print(f"[{durum}] {gorev}: {alinan}/{tam} — {mesaj}")


def oku(yol):
    p = KOK / yol
    # is_file(): ogrenci bazen dosya yerine AYNI ADLA KLASOR olusturuyor
    # (ornegin "sonuc/g1.txt/g1.txt"). exists() bunu dosya sanip read_bytes()
    # ile cokuyor ve TUM degerlendirme sifirlaniyordu.
    if not p.is_file():
        return None
    try:
        ham = p.read_bytes()
    except OSError:
        return None
    # Windows'ta PowerShell'in ">" yonlendirmesi UTF-16 yazar; Not Defteri de
    # UTF-8'e BOM ekler. Bunlari cozmezsek ogrencinin dogru cikti dosyasi
    # taninmaz ve haksiz puan kaybi olur.
    if ham[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ham.decode("utf-16", errors="replace")
    return ham.decode("utf-8-sig", errors="replace")


def ogrno_al():
    icerik = oku("ogrno.txt")
    if icerik is None:
        return None
    icerik = icerik.strip()
    return icerik if icerik.isdigit() else None


def sayi_var(metin, deger):
    return re.search(rf"(?<!\d){deger}(?!\d)", metin) is not None


DB_ADI = "vtysdb"


def mongosh_hedefi():
    """mongosh'a verilecek baglanti dizesi; veritabani adi SART.

    MONGO_URI veritabani yolu tasimiyor (mongodb://localhost:27017).
    Ogrenci betigini foyde 'mongosh vtysdb' ile calistirdigi icin dosyanin
    basindaki getSiblingDB satirini silip gectiginde betik CI'da 'test'
    veritabanina yaziyordu: kendi makinesinde sorunsuz calisan dogru bir
    teslim, Gorev 1'in uc denetiminden de (14 puan) sessizce sifir aliyordu.
    Hedefe veritabani adini biz ekliyoruz; betikteki getSiblingDB satiri
    varsa zararsiz sekilde ayni veritabanini secer.
    """
    uri = os.environ.get("MONGOSH_URI", MONGO_URI).rstrip("/")
    temel, ayrac, sorgu = uri.partition("?")
    if "/" not in temel.split("://", 1)[-1]:
        temel = f"{temel}/{DB_ADI}"
    return temel + ayrac + sorgu


def mongosh_calistir(betik):
    """Bir mongosh betiğini stdin üzerinden çalıştırır."""
    cmd = MONGOSH.split() + ["--quiet", mongosh_hedefi()]
    r = subprocess.run(cmd, input=betik, capture_output=True,
                       text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr)


# ------------------------------------------------------------- Görev 1
def kontrol_g1(db, t):
    dosya = oku("mongo/g1_crud.js")
    if not dosya:
        kaydet("Görev 1 (CRUD)", 0, 20, "mongo/g1_crud.js bulunamadı.")
        return
    kod, cikti = mongosh_calistir(dosya)
    puan = 0
    mesajlar = []
    if kod != 0:
        mesajlar.append(f"Betik hatayla bitti: {cikti.strip().splitlines()[-1] if cikti.strip() else kod}")

    yeni = db.uyeler.find_one({"_id": 9001})
    if yeni and isinstance(yeni.get("telefonlar"), list) and yeni["telefonlar"]:
        puan += 5
    else:
        mesajlar.append("_id 9001'li yeni üye (telefonlar dizisiyle) bulunamadı.")

    u10 = db.uyeler.find_one({"_id": 10})
    if u10 and u10.get("dogum_yili") == 1999:
        puan += 5
    else:
        mesajlar.append("Üye 10'un dogum_yili 1999 olarak güncellenmemiş.")

    if db.uyeler.find_one({"_id": 20}) is None:
        puan += 4
    else:
        mesajlar.append("Üye 20 silinmemiş.")

    oksuz = sum(1 for k in t["kayitlar"] if k["uye_id"] == 20)
    icerik = oku("sonuc/g1.txt") or ""
    if icerik and sayi_var(icerik, oksuz):
        puan += 6
        mesajlar.append(f"Öksüz kayıt gözlemi doğru ({oksuz} kayıt sahipsiz kaldı"
                        " — MongoDB'de yabancı anahtar yok!).")
    else:
        mesajlar.append("sonuc/g1.txt'de öksüz kayıt sayısı görünmüyor "
                        "(üye 20 silindikten sonra kayıtları saydınız mı?).")
    kaydet("Görev 1 (CRUD)", puan, 20, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 2
def kontrol_g2(db, t):
    dosya = oku("mongo/g2_sorgular.js") or ""
    icerik = oku("sonuc/g2.txt") or ""
    puan = 0
    mesajlar = []

    # Foy once Gorev 1'i (uye ekle / guncelle / sil) sonra Gorev 2'nin
    # sayim sorgularini yaptiriyor. Dolayisiyla ogrencinin olctugu sayilar
    # KURULUM verisininkiler degil, CRUD'dan SONRAKI canli durumunkilerdir:
    #   * uye 10'un dogum yili 1999'a cekiliyor,
    #   * uye 20 siliniyor (telefonlariyla birlikte),
    #   * ogrenci kendini uye 9001 olarak kendi dogum yiliyla ekliyor.
    # Beklenen degeri yalnizca ham veriden hesaplamak, foyun kendi sirasini
    # izleyen ogrenciyi cezalandiriyordu (2.1 ve 2.3, 10 puan). Iki sira da
    # gecerli bir calisma oldugu icin HER IKI deger de kabul edilir.
    tel_map = Counter()
    for tel in t["telefonlar"]:
        tel_map[tel["uye_id"]] += 1
    ham = (
        sum(1 for u in t["uyeler"] if u["dogum_yili"] >= 2000),
        sum(1 for d in t["dersler"] if d["ucret"] > 500),
        sum(1 for u in t["uyeler"] if tel_map[u["uye_id"]] == 3),
        Counter(k["ders_id"] for k in t["kayitlar"]).most_common(1)[0][1],
    )
    try:
        enc = list(db.kayitlar.aggregate([
            {"$group": {"_id": "$ders_id", "adet": {"$sum": 1}}},
            {"$sort": {"adet": -1}}, {"$limit": 1}]))
        canli = (
            db.uyeler.count_documents({"dogum_yili": {"$gte": 2000}}),
            db.dersler.count_documents({"ucret": {"$gt": 500}}),
            db.uyeler.count_documents({"telefonlar": {"$size": 3}}),
            enc[0]["adet"] if enc else ham[3],
        )
    except Exception:
        canli = ham

    if not icerik:
        kaydet("Görev 2 (Sorgular)", 0, 30, "sonuc/g2.txt bulunamadı.")
        return
    for no, (a, b) in enumerate(zip(ham, canli), start=1):
        if sayi_var(icerik, a) or sayi_var(icerik, b):
            puan += 5
        else:
            mesajlar.append(f"2.{no}: beklenen değer transkriptte yok.")

    anahtarlar = [("countDocuments", 3), (r"\$gte", 2), (r"\$size", 2),
                  ("aggregate", 2), (r"\$group", 1)]
    for desen, p in anahtarlar:
        if re.search(desen, dosya):
            puan += p
    if puan < 30 and not mesajlar:
        mesajlar.append("g2_sorgular.js'de beklenen operatörlerin bir kısmı eksik "
                        "(countDocuments, $gte, $size, aggregate, $group).")
    kaydet("Görev 2 (Sorgular)", min(puan, 30), 30,
           " ".join(mesajlar) or "Dört sorgunun kanıtı ve operatörleri tam.")


# ------------------------------------------------------------- Görev 3
def kontrol_g3(t):
    icerik = oku("sonuc/g3.md") or ""
    puan = 0
    mesajlar = []
    if not icerik:
        kaydet("Görev 3 (Karşılaştırma)", 0, 15, "sonuc/g3.md bulunamadı.")
        return
    b24 = Counter(k["ders_id"] for k in t["kayitlar"]).most_common(1)[0][1]
    if sayi_var(icerik, b24):
        puan += 8
    else:
        mesajlar.append("İki dünyada da bulmanız gereken ortak değer "
                        "(en çok kaydı olan dersin kayıt sayısı) raporda yok.")
    if len(icerik.strip()) >= 400 and "JOIN" in icerik.upper():
        puan += 7
    else:
        mesajlar.append("Rapor kısa ya da SQL tarafı (JOIN'li sorgu) eksik.")
    kaydet("Görev 3 (Karşılaştırma)", puan, 15, " ".join(mesajlar))


# ------------------------------------------------------------- Görev 4
def kontrol_g4(t):
    icerik = oku("sonuc/g4.txt") or ""
    puan = 0
    mesajlar = []
    if not icerik:
        kaydet("Görev 4 (Redis)", 0, 20, "sonuc/g4.txt bulunamadı.")
        return
    toplam = len(t["kayitlar"])
    if re.search(r"SET\b", icerik, re.IGNORECASE) and sayi_var(icerik, toplam):
        puan += 8
    else:
        mesajlar.append("Toplam kayıt sayınızın Redis'e SET edildiği görünmüyor.")
    if re.search(r"EXPIRE|TTL", icerik, re.IGNORECASE):
        puan += 6
    else:
        mesajlar.append("EXPIRE/TTL kanıtı eksik.")
    if re.search(r"INCR", icerik, re.IGNORECASE) and sayi_var(icerik, 3):
        puan += 6
    else:
        mesajlar.append("INCR sayacının 3'e ulaştığı görünmüyor.")
    kaydet("Görev 4 (Redis)", puan, 20, " ".join(mesajlar) or "Redis kanıtları tam.")


def ogrenci_metni(markdown):
    """Markdown'dan kod bloklarini atip ogrencinin KENDI yazdigi metni birakir.

    Yapay zekanin urettigi SQL'i yapistirip tek satir elestiri yazmayan
    teslimler yalnizca uzunluga bakildiginda esigi gecip tam puan aliyordu
    (gercek teslimlerde tespit edildi). Puan artik duz metne gore verilir.
    """
    m = markdown or ""
    m = re.sub(r"```.*?```", " ", m, flags=re.S)
    m = re.sub(r"```.*", " ", m, flags=re.S)
    m = re.sub(r"^\s{4,}\S.*$", " ", m, flags=re.M)
    m = re.sub(r"`[^`]*`", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def kontrol_ai():
    icerik = oku("sonuc/ai_elestiri.md")
    if not icerik or len(ogrenci_metni(icerik)) < 300:
        kaydet("AI Köşesi", 0, 10,
               "sonuc/ai_elestiri.md yok ya da eleştiri metniniz 300 karakterden kısa "
               "(yapıştırdığınız kod blokları sayılmaz). Föyde istenen iki "
               "somut eleştiriyi yazdığınızda bu uzunluk zaten aşılır "
               "(içerik ayrıca asistan tarafından okunur).")
    else:
        kaydet("AI Köşesi", 10, 10,
               "Dosya teslim edildi (isabet puanı asistan değerlendirmesiyle kesinleşir).")


# ------------------------------------------------------------- ana akış
def main():
    print("=" * 64)
    print("Föy 07 — Otomatik Değerlendirme")
    print("=" * 64)

    ogrno = ogrno_al()
    if not ogrno:
        print("HATA: ogrno.txt bulunamadı ya da geçerli bir numara içermiyor.")
        sys.exit(1)
    print(f"Öğrenci no: {ogrno} (veri seti bu numaradan yeniden üretiliyor)\n")

    t = uret(ogrno)
    kod, cikti = mongosh_calistir(mongo_js(t))
    if kod != 0:
        print(f"HATA: doküman modeli kurulamadı:\n{cikti}")
        sys.exit(2)

    db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)[DB_ADI]

    kontrol_g1(db, t)
    kontrol_g2(db, t)
    kontrol_g3(t)
    kontrol_g4(t)
    kontrol_ai()

    alinan = sum(s[1] for s in SONUCLAR)
    tam = sum(s[2] for s in SONUCLAR)
    print("\n" + "=" * 64)
    print(f"TOPLAM (otomatik kontrol edilen kısım): {alinan}/{tam}")
    print("Rapor metinleri ve AI köşesi asistan tarafından ayrıca")
    print("değerlendirilir.")
    print("=" * 64)

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write("## Föy 07 — Otomatik Değerlendirme\n\n")
            f.write("| Bileşen | Puan | Açıklama |\n|---|---|---|\n")
            for gorev, a, tp, m in SONUCLAR:
                f.write(f"| {gorev} | {a}/{tp} | {m} |\n")
            f.write(f"| **Toplam** | **{alinan}/{tam}** | |\n")

    sys.exit(0 if alinan == tam else 1)


if __name__ == "__main__":
    main()
