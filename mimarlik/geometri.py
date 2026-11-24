"""Dış kontur poligonunu okunan sayılardan kurma (cm, DXF koordinatı: y yukarı).

Krokinin piksel boyları kullanılmaz (kroki ölçekli değil); yalnızca kenar SIRASI ve YÖNÜ krokiden gelir.
Boyu sayılardan çıkmayan kenar:
  * bir eksende tek bilinmeyen kenar varsa kapanmadan hesaplanır ("hesaplandi"); o eksenin kapanması
    "doğrulanamadı" sayılır, "tutuyor" değil (hesaplanan kenar farkı yutar: hatalı çizim gizlenirdi, 01–02),
  * değilse bilinen kenarların cm/px oranının medyanıyla piksel boyundan tahmin edilir ("tahmin").
Kenar boyu kuralları (S1 duvar–kapı–duvar, S3 tek sayı köşeden köşeye) varsayimlar.py'de.
"""

import math
import statistics
from dataclasses import dataclass

from mimarlik import varsayimlar
from mimarlik.birlestirme import SonOlcu
from mimarlik.eslestirme import Kenar, KenarSonucu, Nokta


@dataclass(frozen=True)
class ParcaPlani:
    parca_id: str
    tur: str                 # "duvar" | "aciklik"
    boy: float               # cm
    deger: int | None        # bu parçaya okunan değer (yoksa None: boy türetildi)


@dataclass(frozen=True)
class KenarPlani:
    kenar_id: str
    yon: Nokta               # birim vektör, DXF koordinatı
    boy: float
    durum: str               # "olcu" | "hesaplandi" | "tahmin" | "kismen_tahmin"
    tek_sayi_tamami: bool    # S3 uygulandı
    emin: bool               # boy yalnızca "emin" ölçülerden geldi
    parcalar: tuple[ParcaPlani, ...]
    bas: Nokta
    bit: Nokta


@dataclass(frozen=True)
class Plan:
    kenarlar: tuple[KenarPlani, ...]               # kontur sırasıyla
    kapanma: dict                                  # {"yatay": {...}, "dikey": {...}}
    olcek_cm_px: float | None
    ic_duvarlar: tuple[tuple[str, Nokta, Nokta], ...]  # konturda olmayan bulunan kenarlar, ölçekten (cm)
    notlar: tuple[str, ...]
    iptaller: tuple[tuple[Nokta, Nokta], ...] = ()     # X ile iptal edilen duvar parçaları, ölçekten (cm)
    kapilar: tuple[tuple[Nokta, str, int], ...] = ()    # kapı kuralının boşlukları: (orta nokta cm, kaynak, değer)


def _px(kenar: Kenar) -> float:
    return math.dist(kenar.parcalar[0].bas, kenar.parcalar[-1].bit)


def _dondur(v: Nokta, aci_derece: float) -> Nokta:
    """Görüntü vektörünü eksen açısı kadar geri döndürür (yatay duvarlar x eksenine oturur)."""
    a = math.radians(aci_derece)
    return (v[0] * math.cos(a) + v[1] * math.sin(a), -v[0] * math.sin(a) + v[1] * math.cos(a))


def _yon(kenar: Kenar, aci: float) -> Nokta:
    a, b = kenar.parcalar[0].bas, kenar.parcalar[-1].bit
    ux, uy = _dondur((b[0] - a[0], b[1] - a[1]), aci)
    if kenar.yon == "yatay":
        return (1.0 if ux >= 0 else -1.0, 0.0)
    return (0.0, -1.0 if uy >= 0 else 1.0)   # görüntüde y aşağı, DXF'te yukarı


def _parca_degerleri(olculer: list[SonOlcu]) -> dict[str, SonOlcu]:
    """Parça başına tek ölçü: önce emin olan, sonra listedeki ilk."""
    secilen: dict[str, SonOlcu] = {}
    for o in olculer:
        if o.parca_id is None:
            continue
        onceki = secilen.get(o.parca_id)
        if onceki is None or (o.emin and not onceki.emin):
            secilen[o.parca_id] = o
    return secilen


def _parcalara_dagit(kenar: Kenar, boy: float, degerler: list[int | None], tamami: bool) -> list[float]:
    pxler = [math.dist(p.bas, p.bit) for p in kenar.parcalar]
    if not tamami and all(d is not None for d in degerler):
        return [float(d) for d in degerler]
    if not tamami and any(d is not None for d in degerler):
        # okunan sayı her zaman korunur; sayısız parçalar kalanı piksel oranıyla paylaşır (kalan < 0 ise 0)
        kalan = max(0.0, boy - sum(d for d in degerler if d is not None))
        bos_px = sum(px for px, d in zip(pxler, degerler) if d is None) or 1.0
        return [float(d) if d is not None else kalan * px / bos_px for px, d in zip(pxler, degerler)]
    toplam = sum(pxler) or 1.0
    return [boy * px / toplam for px in pxler]


def _fark_notu(eksen: str, fark: float, hesaplanan: list[str]) -> dict:
    """durum: "tutuyor" | "kapanmiyor" | "dogrulanamadi" (eksende kapanmadan hesaplanan kenar var)."""
    if hesaplanan:
        return {"fark_cm": round(fark, 1), "tutuyor": False, "durum": "dogrulanamadi", "hesaplanan": hesaplanan,
                "not": f"{eksen} doğrulanamadı: {', '.join(hesaplanan)} kapanmadan hesaplandı"}
    tutuyor = abs(fark) <= varsayimlar.KAPANMA_TOLERANSI
    metin = "tolerans içinde" if tutuyor else "kapanmıyor"
    return {"fark_cm": round(fark, 1), "tutuyor": tutuyor, "durum": "tutuyor" if tutuyor else "kapanmiyor",
            "hesaplanan": [], "not": f"{eksen} fark {abs(fark):.0f} cm, {metin}"}


def _olcek(kenarlar, secilen) -> float | None:
    """Sayısı okunan bütün kenarların (konturda olsun olmasın) cm/px oranlarının medyanı."""
    oranlar = []
    for k in kenarlar:
        boy, _ = varsayimlar.kenar_boyu([secilen[p.id].deger if p.id in secilen else None for p in k.parcalar])
        if boy is not None and _px(k) > 0:
            oranlar.append(boy / _px(k))
    return statistics.median(oranlar) if oranlar else None


def _olcekten(sonuc: KenarSonucu, olcek: float | None, p0: Nokta):
    """(konturda olmayan kenarlar, iptaller, kapılar): p0 pikseli (0, 0) olacak şekilde ölçekten cm'ye."""
    if olcek is None:
        return (), (), ()

    def cm(q):
        x, y = _dondur((q[0] - p0[0], q[1] - p0[1]), sonuc.eksen_acisi_derece)
        return (x * olcek, -y * olcek)

    ic = tuple((k.id, cm(k.parcalar[0].bas), cm(k.parcalar[-1].bit)) for k in sonuc.kenarlar if not k.konturda)
    kapilar = tuple((cm(((k.bas[0] + k.bit[0]) / 2, (k.bas[1] + k.bit[1]) / 2)), k.kaynak, k.deger)
                    for k in sonuc.kapilar)
    return ic, tuple((cm(i.silinen[0]), cm(i.silinen[1])) for i in sonuc.iptaller), kapilar


def plan_kur(sonuc: KenarSonucu, olculer: list[SonOlcu], h: float) -> Plan:
    sozluk = {k.id: k for k in sonuc.kenarlar}
    kontur = [sozluk[i] for i in sonuc.kontur_sirasi]
    secilen = _parca_degerleri(olculer)
    notlar = []
    olcek = _olcek(sonuc.kenarlar, secilen)
    if not kontur:
        # bulunan kenarlar yine de (ölçekten) KONTROL'de görünsün: kullanıcı neyin bulunduğunu görür
        p0 = sonuc.kenarlar[0].parcalar[0].bas if sonuc.kenarlar else (0.0, 0.0)
        ic, iptaller, kapilar = _olcekten(sonuc, olcek, p0)
        return Plan((), {}, olcek, ic, ("dış kontur bulunamadı",), iptaller, kapilar)

    kayit = {}
    for k in kontur:
        degerler = [secilen[p.id].deger if p.id in secilen else None for p in k.parcalar]
        boy, tamami = varsayimlar.kenar_boyu(degerler)
        emin = all(secilen[p.id].emin for p in k.parcalar if p.id in secilen)
        kayit[k.id] = {"degerler": degerler, "boy": boy, "tamami": tamami, "emin": emin,
                       "durum": "olcu" if boy is not None else None, "yon": _yon(k, sonuc.eksen_acisi_derece)}

    if olcek is None:
        notlar.append("hiçbir kenarın boyu okunamadı: ölçek yok, piksel boyları cm sayıldı")

    for eksen, i in (("yatay", 0), ("dikey", 1)):
        kenarlar = [k for k in kontur if kayit[k.id]["yon"][i] != 0]
        bilinmeyen = [k for k in kenarlar if kayit[k.id]["boy"] is None]
        if len(bilinmeyen) == 1:
            k = bilinmeyen[0]
            isaret = kayit[k.id]["yon"][i]
            gerekli = -sum(kayit[b.id]["boy"] * kayit[b.id]["yon"][i] for b in kenarlar if b is not k) / isaret
            okunan = sum(d for d in kayit[k.id]["degerler"] if d is not None)
            if gerekli > 0 and gerekli >= okunan:
                kayit[k.id].update(boy=gerekli, durum="hesaplandi", emin=False)
                continue
            notlar.append(f"{k.id}: kapanmadan hesaplanan boy {gerekli:.0f} cm, okunan parçaların toplamından "
                          f"({okunan} cm) küçük ya da ≤ 0; ölçekten tahmin edildi")
        for k in bilinmeyen:
            r = kayit[k.id]
            o = olcek or 1.0
            dolu = [(p, d) for p, d in zip(k.parcalar, r["degerler"]) if d is not None]
            if dolu:
                boy = sum(d for _, d in dolu) + o * sum(math.dist(p.bas, p.bit)
                                                        for p, d in zip(k.parcalar, r["degerler"]) if d is None)
                r.update(boy=boy, durum="kismen_tahmin", emin=False)
            else:
                r.update(boy=o * _px(k), durum="tahmin", emin=False)

    planlar, p = [], (0.0, 0.0)
    for k in kontur:
        r = kayit[k.id]
        bit = (p[0] + r["yon"][0] * r["boy"], p[1] + r["yon"][1] * r["boy"])
        boylar = _parcalara_dagit(k, r["boy"], r["degerler"], r["tamami"])
        parcalar = tuple(ParcaPlani(pp.id, pp.tur, b, d) for pp, b, d in zip(k.parcalar, boylar, r["degerler"]))
        planlar.append(KenarPlani(k.id, r["yon"], r["boy"], r["durum"], r["tamami"], r["emin"], parcalar, p, bit))
        p = bit

    kapanma = {eksen: _fark_notu(eksen, p[i], [k.id for k in kontur
                                                if kayit[k.id]["durum"] == "hesaplandi" and kayit[k.id]["yon"][i] != 0])
               for eksen, i in (("yatay", 0), ("dikey", 1))}

    ic, iptaller, kapilar = _olcekten(sonuc, olcek, kontur[0].parcalar[0].bas)
    return Plan(tuple(planlar), kapanma, olcek, ic, tuple(notlar), iptaller, kapilar)
