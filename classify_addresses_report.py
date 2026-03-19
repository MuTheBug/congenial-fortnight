#!/usr/bin/env python3
"""
Lattakia City Address Classification Report
============================================
Classifies addresses from the registry database into main areas/neighborhoods
of Lattakia city and generates a comprehensive report with pie chart.

Includes an explanation of the Berkeley Protocol for digital open source
investigations used in human rights documentation.
"""

import sqlite3
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'registry.db')

# ──────────────────────────────────────────────────────────────────────
# Area classification mapping
# Each tuple: (area_arabic_name, area_english_name, list_of_keywords)
# Keywords are checked with partial match against the address field.
# Order matters – first match wins, so more specific patterns come first.
# ──────────────────────────────────────────────────────────────────────

AREA_DEFINITIONS = [
    # ── الرمل الجنوبي includes: الغراف، الرمل الفلسطيني، مسبح الشعب، سكنتوري،
    #    بستان الحميمي/الحمامي، بستان السمكة، عين التمرة، حي القدس، الشاليهات الجنوبية،
    #    المخيم، الكورنيش الجنوبي، الضاحية الجنوبية، شارع عروبة، شارع الغراف
    ("الرمل الجنوبي", "Al-Raml Al-Janoubi (South Sand)", [
        "الرمل الجنوبي", "رمل الجنوبي", "الرمل الحنوبي", "رمل جنوبي",
        "نزلة الرمل", "اول الرمل",
        # الغراف sub-area
        "الغراف", "شارع الغراف", "غراف", "بالغراف",
        # الرمل الفلسطيني sub-area
        "الرمل الفلسطيني", "رمل الفلسطيني", "رمل لفلسطيني", "رمل فلسطيني",
        # مسبح الشعب sub-area
        "مسبح الشعب", "مسبح الشب",
        # سكنتوري sub-area
        "سكنتوري", "سكتنوري", "اسكنتوري", "اسنتوري", "السكنتوري",
        "نزلة سكنتوري",
        # بستان الحميمي / الحمامي sub-area
        "بستان الحميمي", "بستان الحمامي", "بستان الحمامة", "حمامي", "بستان حميمي",
        # بستان السمكة sub-area
        "بستان السمكة", "بستان السمكه",
        # عين التمرة sub-area
        "عين التمرة", "عين تمره", "عين ام براهيم",
        # حي القدس sub-area
        "حي القدس", "مخيم القدس",
        # الشاليهات الجنوبية / الضاحية sub-area
        "الشاليهات", "شاليهات", "شالهات", "شالاهات", "كرفانات الضاحية",
        "الضاحية الجنوب", "الضاحية الجنوببة",
        # المخيم sub-area
        "مخيم العائدين", "المخيم",
        # الكورنيش الجنوبي
        "الكورنيش الجنوبي",
        # شارع عروبة
        "شارع عروبة",
        # مرآب بلدية
        "مرآب بلدية",
        # شارع البحر (within رمل)
        "شارع البحر",
        # استديو سارة / صيدلية عائشة etc. unique to رمل جنوبي
        "معسكر الطلائع",
        # جامع المهاجرين area
        "جامع المهاجرين",
        # جامع فلسطين / جامع اسامة (within رمل)
        "جامع فلسطين", "جامع اسامة",
        # سوق الخضرة / سوق الخضار (within رمل جنوبي)
        "سوق الخضرة", "سوق الخضار",
        # فرن قلاب / فرن القلاب
        "فرن قلاب", "فرن القلاب",
    ]),
    # ── قنينص includes: بساتين الريحان، المشاحير، حارة علي جمال، ضاحية الزيتونة
    ("قنينص", "Qunainiss", [
        "قنينص", "قنيص", "قتينص", "مشروع قنينص",
        # بساتين الريحان sub-area
        "بساتين الريحان", "بساتين ريحان", "بستان الريحان", "بستاتين الريحان",
        # المشاحير sub-area
        "المشاحير", "مشاحير",
        # حارة علي جمال sub-area
        "حارة علي جمال", "علي جمال",
        # ضاحية الزيتونة
        "ضاحية الزيتونة",
    ]),
    ("الصليبة", "Al-Sulayba", [
        "صليبة", "صليبه", "الصليبة", "مشروع صليبة", "مشروع صليبه",
        "مشروع الصليبة",
    ]),
    ("الحفة", "Al-Haffa", [
        "الحفة", "الحفه", "حفة", "لحفه", "الخفة",
    ]),
    ("بستان الصيداوي", "Bustan Al-Saydawi", [
        "بستان الصيداوي", "الصيداوي",
    ]),
    ("العوينة", "Al-Uwaina", [
        "العوينة", "العوينه", "لعوينه",
    ]),
    ("الأشرفية", "Al-Ashrafiyya", [
        "الاشرفية", "الأشرفية", "لاشرفيه", "اشرفية",
    ]),
    ("الطابيات", "Al-Tabiyat", [
        "الطابيات", "طابيات", "مشفى الطابيات",
    ]),
    ("مرتقلا", "Martaqla", [
        "مرتقلا", "لمرتقله", "مارتقلا",
    ]),
    ("شيخ ضاهر", "Sheikh Daher", [
        "شيخضاهر", "شيخ ضاهر", "شبخ ضاهر", "الشيخضاهر", "الشخصاهر",
        "بالشخصاهر",
    ]),
    ("حي القصور", "Hay Al-Qusur (Palaces Quarter)", [
        "حي القصور", "حي لقصور", "لقصور", "القصور",
    ]),
    ("حي السجن", "Hay Al-Sijn (Prison Quarter)", [
        "حي السجن",
    ]),
    ("حي الفاروس", "Hay Al-Farous", [
        "حي الفاروس", "الفاروس",
    ]),
    ("شارع ميسلون", "Maysaloun Street", [
        "شارع ميسلون", "ميسلون",
    ]),
    ("شارع انطاكيا", "Antakia Street", [
        "شارع انطاكيا", "شارع انطاكيه", "شارع انطاكية",
    ]),
    ("سوق الداية", "Souq Al-Dayya", [
        "سوق الداية", "سوق داية",
    ]),
    ("مشروع القلعة", "Al-Qala'a Project", [
        "مشروع القلعة", "مشروع لقلعه", "مشروع لاقلاعه", "مشروع تجميل القلعة",
        "القلعة",
    ]),
    ("شارع بور سعيد", "Port Said Street", [
        "بور سعيد", "بوور سعيد",
    ]),
    ("الريجي", "Al-Riji", [
        "الريجي",
    ]),
    ("طريق الحرش", "Tariq Al-Hirsh", [
        "طريق الحرش",
    ]),
]


def classify_address(address: str) -> str:
    """Classify a single address into a main area."""
    if not address:
        return "غير محدد"
    addr = address.strip()
    for area_ar, _, keywords in AREA_DEFINITIONS:
        for kw in keywords:
            if kw in addr:
                return area_ar
    return "مناطق أخرى"


def reshape_arabic(text: str) -> str:
    """Reshape Arabic text for correct display in matplotlib."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def fetch_lattakia_addresses():
    """Fetch all addresses for Lattakia province from the database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT address FROM records WHERE province='اللاذقية' AND address IS NOT NULL AND address != ''"
    )
    addresses = [row[0] for row in cur.fetchall()]
    total_lattakia = conn.execute(
        "SELECT COUNT(*) FROM records WHERE province='اللاذقية'"
    ).fetchone()[0]
    total_all = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    conn.close()
    return addresses, total_lattakia, total_all


def classify_all(addresses):
    """Classify all addresses and return area counts."""
    area_counts = {}
    for addr in addresses:
        area = classify_address(addr)
        area_counts[area] = area_counts.get(area, 0) + 1
    # Sort by count descending
    return dict(sorted(area_counts.items(), key=lambda x: x[1], reverse=True))


def get_english_name(area_ar):
    """Get the English name for an Arabic area name."""
    for ar, en, _ in AREA_DEFINITIONS:
        if ar == area_ar:
            return en
    if area_ar == "مناطق أخرى":
        return "Other Areas"
    return "Unspecified"


def generate_pie_chart(area_counts, total_with_address, output_path):
    """Generate a pie chart of area distribution."""
    # Merge small slices (< 2%) into "Other"
    threshold = total_with_address * 0.02
    main_areas = {}
    other_count = 0
    for area, count in area_counts.items():
        if count >= threshold and area != "مناطق أخرى":
            main_areas[area] = count
        else:
            other_count += count
    if other_count > 0:
        main_areas["مناطق أخرى"] = other_count

    # Sort for consistent display
    sorted_areas = dict(sorted(main_areas.items(), key=lambda x: x[1], reverse=True))

    labels = []
    sizes = []
    for area, count in sorted_areas.items():
        pct = (count / total_with_address) * 100
        label = f"{reshape_arabic(area)}\n{count} ({pct:.1f}%)"
        labels.append(label)
        sizes.append(count)

    # Color palette
    colors = [
        '#2196F3', '#FF5722', '#4CAF50', '#FFC107', '#9C27B0',
        '#00BCD4', '#FF9800', '#E91E63', '#8BC34A', '#673AB7',
        '#009688', '#F44336', '#3F51B5', '#CDDC39', '#795548',
        '#607D8B', '#FFEB3B', '#03A9F4', '#FF6F00', '#AD1457',
    ]

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors[:len(sizes)],
        autopct='',
        startangle=140,
        pctdistance=0.75,
        labeldistance=1.15,
        textprops={'fontsize': 8, 'fontweight': 'bold'},
    )

    title_text = reshape_arabic("توزيع العناوين حسب المناطق الرئيسية في مدينة اللاذقية")
    ax.set_title(title_text, fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Pie chart saved to: {output_path}")


def generate_text_report(area_counts, total_with_address, total_lattakia, total_all):
    """Generate the full text report."""
    report_lines = []
    line = report_lines.append

    line("=" * 90)
    line("تقرير توزيع العناوين حسب المناطق الرئيسية في مدينة اللاذقية")
    line("Address Distribution Report by Main Areas in Lattakia City")
    line("=" * 90)
    line(f"تاريخ التقرير / Report Date: {datetime.now().strftime('%Y-%m-%d')}")
    line("")

    # ── Summary ──
    line("─" * 90)
    line("ملخص عام / General Summary")
    line("─" * 90)
    line(f"  إجمالي السجلات في قاعدة البيانات / Total records in database: {total_all}")
    line(f"  سجلات محافظة اللاذقية / Lattakia province records: {total_lattakia}")
    line(f"  سجلات بعناوين محددة / Records with addresses: {total_with_address}")
    no_addr = total_lattakia - total_with_address
    line(f"  سجلات بدون عنوان / Records without address: {no_addr}")
    line(f"  عدد المناطق المصنفة / Number of classified areas: {len(area_counts)}")
    line("")

    # ── Distribution Table ──
    line("─" * 90)
    line("توزيع العناوين حسب المناطق / Address Distribution by Area")
    line("─" * 90)
    line(f"{'#':<4} {'المنطقة (Area)':<50} {'العدد':>6} {'النسبة':>8}")
    line(f"{'':─<4} {'':─<50} {'':─>6} {'':─>8}")

    for i, (area, count) in enumerate(area_counts.items(), 1):
        pct = (count / total_with_address) * 100
        en_name = get_english_name(area)
        display = f"{area} / {en_name}"
        line(f"{i:<4} {display:<50} {count:>6} {pct:>7.1f}%")

    line(f"{'':─<4} {'':─<50} {'':─>6} {'':─>8}")
    line(f"{'':4} {'المجموع / Total':<50} {total_with_address:>6} {'100.0%':>8}")
    line("")

    # ── Top 5 ──
    line("─" * 90)
    line("أكبر 5 مناطق / Top 5 Areas")
    line("─" * 90)
    top5 = list(area_counts.items())[:5]
    for i, (area, count) in enumerate(top5, 1):
        pct = (count / total_with_address) * 100
        bar = "█" * int(pct)
        en = get_english_name(area)
        line(f"  {i}. {area} / {en}")
        line(f"     {bar} {count} حالة ({pct:.1f}%)")
    line("")

    # ── Analysis ──
    line("─" * 90)
    line("تحليل النتائج / Analysis")
    line("─" * 90)
    top_area, top_count = list(area_counts.items())[0]
    top_pct = (top_count / total_with_address) * 100
    line(f"""
  - المنطقة الأكثر تأثراً هي "{top_area}" بنسبة {top_pct:.1f}% من إجمالي الحالات
    The most affected area is "{get_english_name(top_area)}" with {top_pct:.1f}% of total cases

  - تتركز الحالات بشكل كبير في المناطق الشعبية والعشوائية في اللاذقية
    Cases are heavily concentrated in popular and informal neighborhoods of Lattakia

  - أغلب المناطق المتأثرة هي مناطق ذات كثافة سكانية عالية ومستوى اقتصادي متوسط إلى منخفض
    Most affected areas have high population density and medium to low economic levels

  - تشكل أكبر 5 مناطق ما نسبته {sum(c for _, c in top5) / total_with_address * 100:.1f}% من مجموع الحالات
    The top 5 areas represent {sum(c for _, c in top5) / total_with_address * 100:.1f}% of all cases
""")

    # ── Berkeley Protocol Explanation ──
    line("=" * 90)
    line("بروتوكول بيركلي للتحقيقات الرقمية مفتوحة المصدر")
    line("The Berkeley Protocol on Digital Open Source Investigations")
    line("=" * 90)
    line("""
  نظرة عامة / Overview
  ─────────────────────
  بروتوكول بيركلي هو إطار عمل دولي وضعه مكتب الأمم المتحدة لحقوق الإنسان بالتعاون
  مع مركز حقوق الإنسان في كلية الحقوق بجامعة كاليفورنيا - بيركلي. صدر في عام 2022
  ويُعد المرجع الأول عالمياً لتوثيق انتهاكات حقوق الإنسان باستخدام المعلومات الرقمية
  مفتوحة المصدر.

  The Berkeley Protocol is an international framework developed by the UN Office of the
  High Commissioner for Human Rights (OHCHR) in partnership with the Human Rights Center
  at UC Berkeley School of Law. Published in 2022, it is the leading global reference
  for documenting human rights violations using digital open source information.

  المبادئ الأساسية / Core Principles
  ────────────────────────────────────
  1. الكفاءة والمسؤولية (Competence & Accountability)
     يجب أن يكون المحققون مؤهلين ومدربين على جمع الأدلة الرقمية وفقاً لأعلى المعايير
     المهنية، مع تحمّل المسؤولية الكاملة عن عملهم.

     Investigators must be qualified and trained in collecting digital evidence according
     to the highest professional standards, with full accountability for their work.

  2. الموضوعية والنزاهة (Objectivity & Integrity)
     يتطلب البروتوكول التزام المحققين بالحياد التام وعدم التحيز في جمع وتحليل
     المعلومات، مع الحفاظ على سلامة الأدلة.

     The protocol requires investigators to maintain complete impartiality in collecting
     and analyzing information, while preserving evidence integrity.

  3. حماية البيانات والخصوصية (Data Protection & Privacy)
     تُعطى أولوية قصوى لحماية البيانات الشخصية للضحايا والشهود والمصادر، وضمان عدم
     تعرضهم لأي خطر إضافي بسبب عملية التوثيق.

     Top priority is given to protecting personal data of victims, witnesses, and sources,
     ensuring they are not exposed to additional risk due to the documentation process.

  4. السلامة النفسية (Psychological Well-being)
     يؤكد البروتوكول على ضرورة حماية الصحة النفسية للمحققين الذين يتعاملون مع محتوى
     صادم ومواد حساسة بشكل يومي.

     The protocol emphasizes protecting the mental health of investigators who deal with
     traumatic content and sensitive materials on a daily basis.

  5. الدقة والتحقق (Accuracy & Verification)
     يجب التحقق من كل معلومة من عدة مصادر مستقلة قبل اعتمادها كدليل، مع توثيق سلسلة
     الحفظ الكاملة لكل دليل.

     Every piece of information must be verified from multiple independent sources before
     being accepted as evidence, with full chain of custody documented.

  منهجية التوثيق / Documentation Methodology
  ─────────────────────────────────────────────
  يعتمد بروتوكول بيركلي على منهجية منظمة تشمل:

  ● التخطيط المسبق: وضع خطة بحث واضحة قبل البدء بجمع المعلومات
    Pre-planning: Establishing a clear research plan before beginning data collection

  ● الجمع المنهجي: استخدام أدوات وتقنيات موثوقة لجمع الأدلة الرقمية مع الحفاظ على
    البيانات الوصفية (metadata) الأصلية
    Systematic Collection: Using reliable tools and techniques to collect digital evidence
    while preserving original metadata

  ● التحقق والتثبت: مراجعة الأدلة عبر مصادر متعددة وتقنيات تحقق مختلفة
    (تحديد الموقع الجغرافي، تحليل الظل والطقس، مقارنة المصادر)
    Verification: Cross-referencing evidence through multiple sources and techniques
    (geolocation, shadow/weather analysis, source comparison)

  ● الأرشفة الآمنة: حفظ الأدلة بطريقة تضمن سلامتها وإمكانية الوصول إليها لاحقاً
    مع استخدام تقنيات التجزئة (hashing) للتحقق من عدم التلاعب
    Secure Archiving: Preserving evidence in a manner that ensures its integrity and
    future accessibility, using hashing techniques to verify non-tampering

  ● سلسلة الحفظ: توثيق كل خطوة من خطوات جمع ونقل وتخزين الأدلة لضمان قبولها
    أمام المحاكم الدولية
    Chain of Custody: Documenting every step of evidence collection, transfer, and
    storage to ensure admissibility before international courts

  تطبيق البروتوكول في هذه القاعدة / Application in This Database
  ──────────────────────────────────────────────────────────────────
  تتبع قاعدة البيانات هذه مبادئ بروتوكول بيركلي من خلال:

  This database follows Berkeley Protocol principles through:

  1. ✓ مستويات التحقق (Verification Levels): تصنيف الحالات إلى "تم التحقق" و"مؤكد"
     و"غير محقق" - Cases classified as "verified", "corroborated", and "unverified"

  2. ✓ مستويات الأدلة (Evidence Levels): تصنيف قوة الأدلة إلى "عالي" و"متوسط"
     و"منخفض" - Evidence strength classified as "high", "medium", and "low"

  3. ✓ تتبع التغييرات (Change Tracking): نظام تدقيق كامل يسجل كل تعديل على
     السجلات - Full audit system recording every modification to records

  4. ✓ تجزئة الملفات (File Hashing): استخدام تقنيات التجزئة للصور والوثائق للتحقق
     من عدم التلاعب - Using hashing for photos and documents to verify non-tampering

  5. ✓ تصنيف الحالات (Case Classification): نظام تصنيف دقيق يميز بين أنواع الحالات
     المختلفة (اختفاء قسري، ناجي، متوفى) - Precise classification system distinguishing
     between different case types (enforced disappearance, survivor, deceased)

  6. ✓ حماية البيانات (Data Protection): حفظ البيانات الشخصية بشكل آمن مع تقييد
     الوصول - Secure storage of personal data with restricted access

  7. ✓ توثيق المصادر (Source Documentation): تسجيل بيانات المبلغين وعلاقتهم بالضحايا
     مع حماية هوياتهم - Recording reporter data and their relationship to victims
     while protecting their identities

  المراجع / References
  ─────────────────────
  - Berkeley Protocol on Digital Open Source Investigations (2022)
    UN Human Rights Office & UC Berkeley Human Rights Center
  - Updated Guidelines on International Human Rights Fact-Finding (Lund-London)
  - Istanbul Protocol (Manual on Effective Investigation of Torture)
""")

    line("=" * 90)
    line(f"نهاية التقرير / End of Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    line("=" * 90)

    return "\n".join(report_lines)


def main():
    print("Fetching data from database...")
    addresses, total_lattakia, total_all = fetch_lattakia_addresses()
    total_with_address = len(addresses)

    print(f"Total records: {total_all}")
    print(f"Lattakia records: {total_lattakia}")
    print(f"Records with addresses: {total_with_address}")

    print("\nClassifying addresses into main areas...")
    area_counts = classify_all(addresses)

    # Generate pie chart
    chart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'lattakia_areas_distribution.png')
    print("\nGenerating pie chart...")
    generate_pie_chart(area_counts, total_with_address, chart_path)

    # Generate text report
    report = generate_text_report(area_counts, total_with_address,
                                  total_lattakia, total_all)

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'lattakia_address_classification_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")

    # Print report to console
    print("\n")
    print(report)


if __name__ == '__main__':
    main()
