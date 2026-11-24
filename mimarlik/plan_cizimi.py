"""Plan -> DXF: DUVAR (iç + dış yüz), KAPI, OLCU ve programın emin olmadığı her şey için KONTROL katmanı.

Varsayımlar (varsayimlar.py): çizilen kontur duvarın İÇ yüzü (S6), dış yüz DIS_DUVAR_KALINLIGI kadar dışarıda;
açıklık kapıdır, içeri açılır, menteşe açıklığın kontur yönündeki başında (S1).
Kontur saat yönünde (DXF'te de, y yukarı): dışarısı her kenarın SOLUNDA.
"""

import math

from ezdxf.document import Drawing

from mimarlik import varsayimlar
from mimarlik.birlestirme import SonOlcu
from mimarlik.dxf_yazici import cizgi_ekle, daire_ekle, olcu_ekle, yay_ekle, yazi_ekle, yeni_cizim
from mimarlik.geometri import KenarPlani, Plan
from mimarlik.standartlar import KATMAN_DUVAR, KATMAN_KAPI, KATMAN_KONTROL, KATMAN_OLCU

OLCU_MESAFESI = 40      # ölçü çizgisinin dış yüzden uzaklığı (cm)
NOT_MESAFESI = 90       # KONTROL notlarının dış yüzden uzaklığı (cm)
YAZI = 12               # KONTROL yazı yüksekliği (cm)
ISARET = 12             # KONTROL işaret dairesinin yarıçapı (cm)
LISTE_MESAFESI = 150    # not listesinin planın (işaretler dahil) en sağından uzaklığı (cm)
SATIR = 1.7             # not listesinde satır aralığı (yazı yüksekliği katı)


def _topla(*vektorler):
    return (sum(v[0] for v in vektorler), sum(v[1] for v in vektorler))


def _kat(v, s):
    return (v[0] * s, v[1] * s)


def _normal(k: KenarPlani):
    return (-k.yon[1], k.yon[0])   # sol taraf = dışarısı


def _kapali(plan: Plan) -> bool:
    return bool(plan.kapanma) and all(e["tutuyor"] for e in plan.kapanma.values())


def _parca_araliklari(k: KenarPlani):
    """[(ParcaPlani, baş uzaklığı, bitiş uzaklığı)] kenar başından cm."""
    t, sonuc = 0.0, []
    for p in k.parcalar:
        sonuc.append((p, t, t + p.boy))
        t += p.boy
    return sonuc


def _dis_kose(onceki: KenarPlani | None, k: KenarPlani, nokta, t):
    """Kenarın dış yüzündeki köşe noktası (önceki kenarla dik birleşiyorsa iki normalin toplamı)."""
    if onceki is not None and abs(onceki.yon[0] * k.yon[0] + onceki.yon[1] * k.yon[1]) < 1e-9:
        return _topla(nokta, _kat(_normal(onceki), t), _kat(_normal(k), t))
    return _topla(nokta, _kat(_normal(k), t))


def _duvarlar(doc: Drawing, plan: Plan) -> None:
    t, n = varsayimlar.DIS_DUVAR_KALINLIGI, len(plan.kenarlar)
    kapali = _kapali(plan)
    for i, k in enumerate(plan.kenarlar):
        onceki = plan.kenarlar[i - 1] if (i > 0 or kapali) else None
        sonraki = plan.kenarlar[(i + 1) % n] if (i < n - 1 or kapali) else None
        no = _normal(k)
        dis_bas = _dis_kose(onceki, k, k.bas, t)
        dis_bit = _dis_kose(k, sonraki, k.bit, t) if sonraki is not None else _topla(k.bit, _kat(no, t))
        # dış yüzün kenar yönündeki uzaklıkları (iç köşeye göre): dış köşe iç köşeden önce/sonra olabilir
        uzunluk_bas = (dis_bas[0] - k.bas[0]) * k.yon[0] + (dis_bas[1] - k.bas[1]) * k.yon[1]
        uzunluk_bit = (dis_bit[0] - k.bas[0]) * k.yon[0] + (dis_bit[1] - k.bas[1]) * k.yon[1]
        bosluklar = [(a, b) for p, a, b in _parca_araliklari(k) if p.tur == "aciklik" and b > a]

        def nokta(s, kaydir=0.0):
            return _topla(k.bas, _kat(k.yon, s), _kat(no, kaydir))

        for bas, bit, kaydir in ((0.0, k.boy, 0.0), (uzunluk_bas, uzunluk_bit, t)):
            s = bas
            for a, b in bosluklar:
                if a > s:
                    cizgi_ekle(doc, [(*nokta(s, kaydir), *nokta(a, kaydir))], KATMAN_DUVAR)
                s = max(s, b)
            if bit > s:
                cizgi_ekle(doc, [(*nokta(s, kaydir), *nokta(bit, kaydir))], KATMAN_DUVAR)
        for a, b in bosluklar:
            cizgi_ekle(doc, [(*nokta(a), *nokta(a, t)), (*nokta(b), *nokta(b, t))], KATMAN_DUVAR)  # söveler
            if varsayimlar.ACIKLIK_KAPIDIR:
                w = b - a
                mentese, iceri = nokta(a), _kat(no, -1)
                cizgi_ekle(doc, [(*mentese, *_topla(mentese, _kat(iceri, w)))], KATMAN_KAPI)
                aci_ic = math.degrees(math.atan2(iceri[1], iceri[0]))
                aci_kenar = math.degrees(math.atan2(k.yon[1], k.yon[0]))
                yay_ekle(doc, mentese, w, aci_ic, aci_kenar, KATMAN_KAPI)  # saat yönü tersine: içeriden kenara


def _olculer(doc: Drawing, plan: Plan) -> None:
    """Okunan sayı -> o parçaya OLCU; sayıdan gelmeyen boy -> KONTROL (parça ya da kenar)."""
    uzaklik = varsayimlar.DIS_DUVAR_KALINLIGI + OLCU_MESAFESI
    for k in plan.kenarlar:
        okunan = [p.deger is not None for p in k.parcalar]
        if k.tek_sayi_tamami or not any(okunan):   # tek ölçü bütün kenara
            if k.boy > 0:
                katman = KATMAN_OLCU if k.durum == "olcu" else KATMAN_KONTROL
                olcu_ekle(doc, k.bas, k.bit, uzaklik, katman)
            continue
        for p, a, b in _parca_araliklari(k):
            if b > a:
                katman = KATMAN_OLCU if p.deger is not None else KATMAN_KONTROL
                olcu_ekle(doc, _topla(k.bas, _kat(k.yon, a)), _topla(k.bas, _kat(k.yon, b)), uzaklik, katman)


def _kontrol(doc: Drawing, plan: Plan, olculer: list[SonOlcu], sadece_y2) -> list[str]:
    """KONTROL katmanını doldurur; notların tam metnini döndürür.

    Planın üstüne yalnız numaralı işaret (daire + numara) konur; notların tam metni planın SAĞINDA, numara
    sırasıyla alt alta liste olarak yazılır (AutoCAD Web'de notlar planın üstüne yığılıp okunmuyordu).
    Yeri olmayan notlar (ör. hiçbir parçaya bağlanamayan sayı) yalnız listede, işaretsiz.
    """
    maddeler: list[tuple[str, tuple | None]] = []   # (metin, işaret noktası ya da None)
    yigin: dict[tuple, int] = {}

    def isaretli(metin, nokta, normal=None):
        """İşaret nokta + normal yönünde dış yüzün ötesine; aynı noktadaki işaretler normal boyunca dizilir."""
        if normal is not None:
            sira = yigin.get(nokta, 0)
            yigin[nokta] = sira + 1
            mesafe = varsayimlar.DIS_DUVAR_KALINLIGI + NOT_MESAFESI + sira * ISARET * 2.6
            nokta = _topla(nokta, _kat(normal, mesafe))
        maddeler.append((metin, nokta))

    # kapanmayan eksen: o eksendeki bütün kenarlar + başlangıçla bitiş arasındaki açıklık.
    # Doğrulanamayan eksende (kenar kapanmadan hesaplandı) yalnız hesaplanan kenar işaretlenir (aşağıda).
    for eksen, e in plan.kapanma.items():
        if e["durum"] != "kapanmiyor":
            continue
        i = 0 if eksen == "yatay" else 1
        for k in plan.kenarlar:
            if k.yon[i] != 0:
                cizgi_ekle(doc, [(*k.bas, *k.bit)], KATMAN_KONTROL)
    if plan.kenarlar and not _kapali(plan):
        son = plan.kenarlar[-1].bit
        if math.dist(son, (0.0, 0.0)) > 0:
            cizgi_ekle(doc, [(*son, 0.0, 0.0)], KATMAN_KONTROL)
        baslik = ("KAPANMIYOR" if any(e["durum"] == "kapanmiyor" for e in plan.kapanma.values())
                  else "DOĞRULANAMADI")
        isaretli(f"{baslik}: " + "; ".join(e["not"] for e in plan.kapanma.values()), son)

    # sayıdan gelmeyen kenar boyları
    for k in plan.kenarlar:
        if k.durum == "hesaplandi":   # okunmadı; boyu kapanmayı zorla sağlıyor: kenarın kendisi de işaretli
            cizgi_ekle(doc, [(*k.bas, *k.bit)], KATMAN_KONTROL)
            orta = _topla(k.bas, _kat(k.yon, k.boy / 2))
            isaretli(f"? {k.kenar_id} {k.boy:.0f} cm: okunmadı, kapanmadan hesaplandı", orta, _normal(k))
        elif k.durum != "olcu":
            orta = _topla(k.bas, _kat(k.yon, k.boy / 2))
            isaretli(f"? {k.kenar_id} {k.boy:.0f} cm ({k.durum})", orta, _normal(k))

    # emin olunmayan ölçüler, parçasının ortasına
    yer = {}
    for k in plan.kenarlar:
        for p, a, b in _parca_araliklari(k):
            yer[p.parca_id] = (_topla(k.bas, _kat(k.yon, (a + b) / 2)), _normal(k))
    serbest = []
    for o in olculer:
        if o.emin:
            continue
        metin = f"? {o.deger}: {o.sebep}"
        if o.parca_id in yer:
            isaretli(metin, *yer[o.parca_id])
        else:
            serbest.append(metin if o.parca_id is None else f"{metin} ({o.parca_id}, konturda değil)")
    serbest += [f"? {d}: yalnızca Y2 okudu ({pid})" for d, pid in sadece_y2]
    serbest += [f"! {n}" for n in plan.notlar]

    # konturda olmayan kenarlar (iç duvar ya da kapanmayan konturun parçaları): ölçüsüz, ölçekten
    for kid, a, b in plan.ic_duvarlar:
        cizgi_ekle(doc, [(*a, *b)], KATMAN_KONTROL)
        isaretli(f"{kid} ölçüsüz (konturda değil)", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

    for orta, kaynak, deger in plan.kapilar:   # kapı kuralı: etiket yoksa çıkarım, kullanıcı görsün
        if kaynak == "etiket":
            continue
        isaretli(f"? kapı {deger}: yakında okunan sayıdan", orta)

    for orta in plan.bosluklar:   # kapı adayı ama kanıt yok (etiket / kapı genişliğinde sayı): kullanıcı karar verir
        isaretli("? boşluk: kapı mı? (yakınında K etiketi ya da kapı genişliğinde sayı yok)", orta)

    for a, b in plan.iptaller:   # mimar S5: X = orada duvar yok
        cizgi_ekle(doc, [(*a, *b)], KATMAN_KONTROL)
        isaretli("X: iptal edilmiş duvar", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

    maddeler += [(m, None) for m in serbest]
    if not maddeler:
        return []

    for n, (_, nokta) in enumerate(maddeler, 1):
        if nokta is not None:
            daire_ekle(doc, nokta, ISARET, KATMAN_KONTROL)
            yazi_ekle(doc, str(n), nokta, ISARET * 0.9, KATMAN_KONTROL, ortala=True)

    # liste: planın (işaretler dahil) sağında, üstten aşağı
    noktalar = [p for k in plan.kenarlar for p in (k.bas, k.bit)]
    noktalar += [p for _, a, b in plan.ic_duvarlar for p in (a, b)]
    noktalar += [p for a, b in plan.iptaller for p in (a, b)]
    noktalar += [nokta for _, nokta in maddeler if nokta is not None]
    x = max((p[0] for p in noktalar), default=0.0) + varsayimlar.DIS_DUVAR_KALINLIGI + LISTE_MESAFESI
    y = max((p[1] for p in noktalar), default=0.0)
    yazi_ekle(doc, "KONTROL NOTLARI", (x, y), YAZI * 1.25, KATMAN_KONTROL)
    for n, (metin, _) in enumerate(maddeler, 1):
        yazi_ekle(doc, f"{n}. {metin}", (x, y - (n + 0.5) * YAZI * SATIR), YAZI, KATMAN_KONTROL)
    return [m for m, _ in maddeler]


def ciz(plan: Plan, olculer: list[SonOlcu], sadece_y2=()) -> tuple[Drawing, list[str]]:
    """Döner: (DXF belgesi, KONTROL notları)."""
    doc = yeni_cizim("cm")
    _duvarlar(doc, plan)
    _olculer(doc, plan)
    return doc, _kontrol(doc, plan, olculer, list(sadece_y2))
