import random
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

MESAJLAR = {
    "genel": [
        "Gelirinizin en az %20'sini tasarrufa ayırmanız, finansal güvenlik için temel kuraldır.",
        "Acil durum fonu olarak 3-6 aylık gideriniz kadar birikim bulundurmanız önerilir.",
        "Küçük günlük harcamalar fark edilmese de aylık bütçenizin önemli bir bölümünü oluşturabilir.",
        "Finansal hedef belirlemek, harcama alışkanlıklarınızı bilinçli yönetmenizi sağlar.",
    ],
    "enflasyon": [
        "Yüksek enflasyon dönemlerinde nakit tutmak satın alma gücünüzü eritir.",
        "TL birikimlerinizi enflasyona karşı korumak için çeşitlendirme değerlendirilebilir.",
        "Enflasyon oranının üzerinde getiri sağlayan araçlar reel servetinizi korur.",
        "Kategori bazlı enflasyon farklılık gösterir — en çok etkilenen kalemleri takip edin.",
    ],
    "abonelik": [
        "Kullanmadığınız abonelikleri iptal etmek yıllık binlerce TL tasarruf sağlayabilir.",
        "Döviz bazlı aboneliklerinizin TL maliyeti kur artışıyla birlikte sürekli yükselir.",
        "Aboneliklerinizi yılda en az bir kez gözden geçirmeniz önerilir.",
    ],
    "vergi": [
        "Harcamalarınızın önemli bir kısmı KDV ve ÖTV gibi dolaylı vergilerden oluşur.",
        "Vergi yükünüzü görmek, gerçek harcama maliyetlerinizi anlamanıza yardımcı olur.",
    ],
    "doviz": [
        "Döviz kurundaki dalgalanmalar yurt dışı kaynaklı harcamalarınızı doğrudan etkiler.",
        "Aylık harcamanızın döviz karşılığını bilmek, ekonomik değişimlere hazırlıklı olmanızı sağlar.",
    ],
    "tasarruf": [
        "Önce kendinize ödeyin — gelir gelir gelmez tasarruf payını ayırın, kalanıyla harcayın.",
        "Küçük ama düzenli tasarruflar bileşik büyümeyle uzun vadede büyük fark yaratır.",
        "Tasarruf oranınızı her ay %1 artırmak yıl sonunda önemli bir fark yaratır.",
    ],
}

def get_awareness_message(
    categories: dict = None,
    subscriptions: list = None,
    health_score: int = None
) -> str:
    """
    Kullanıcının profiline göre bağlamsal bilinçlendirme mesajı seçer.
    """
    # Bağlama göre kategori seç
    if health_score and health_score < 50:
        kategori = "tasarruf"
    elif subscriptions and len(subscriptions) >= 3:
        kategori = "abonelik"
    elif categories and categories.get("ulasim", 0) > 3000:
        kategori = "enflasyon"
    elif categories and categories.get("kira", 0) > 0:
        kategori = "doviz"
    else:
        kategori = "genel"

    mesajlar = MESAJLAR.get(kategori, MESAJLAR["genel"])
    secilen = random.choice(mesajlar)

    return f"💡 {secilen}"

def get_daily_tip() -> str:
    """Günlük rastgele finansal ipucu."""
    tum_mesajlar = []
    for mesajlar in MESAJLAR.values():
        tum_mesajlar.extend(mesajlar)
    return f"💡 Günün İpucu: {random.choice(tum_mesajlar)}"


if __name__ == "__main__":
    print("Bağlamsal mesaj testi:")
    print("-" * 40)

    # Abonelik yükü yüksek
    msg = get_awareness_message(subscriptions=[1, 2, 3, 4])
    print(f"Çok abonelik  : {msg}")

    # Ulaşım yüksek
    msg = get_awareness_message(categories={"ulasim": 5000})
    print(f"Yüksek ulaşım : {msg}")

    # Düşük skor
    msg = get_awareness_message(health_score=40)
    print(f"Düşük skor    : {msg}")

    # Genel
    msg = get_awareness_message()
    print(f"Genel         : {msg}")

    print("\nGünlük ipucu:")
    print(get_daily_tip())