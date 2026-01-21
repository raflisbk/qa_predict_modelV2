"""Generate synthetic dataset prompts untuk training AI dalam bahasa Indonesia.

Script ini membuat 10,000 skenario unik yang menggabungkan hari, slot waktu,
skor, dan gaya penulisan untuk optimasi waktu posting media sosial.
"""
import random

import pandas as pd


# --- KONFIGURASI ---
TOTAL_ROWS = 10000
# Output file akan disimpan di folder parent dari scripts
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)  # parent folder (data/)
OUTPUT_FILE = os.path.join(DATA_DIR, "step1_dataset_prompts_id.csv")

# --- 1. DEFINISI DATA ---
DAYS = [
    {"en": "Monday", "id": "Senin"},
    {"en": "Tuesday", "id": "Selasa"},
    {"en": "Wednesday", "id": "Rabu"},
    {"en": "Thursday", "id": "Kamis"},
    {"en": "Friday", "id": "Jumat"},
    {"en": "Saturday", "id": "Sabtu"},
    {"en": "Sunday", "id": "Minggu"},
]

TIME_SLOTS = [
    {
        "window": "06:00 - 09:00",
        "label_en": "Morning Rush",
        "label_id": "Pagi Hari",
        "insight_en": "users checking phones before work",
        "insight_id": "pengguna mengecek ponsel sebelum bekerja"
    },
    {
        "window": "09:00 - 12:00",
        "label_en": "Mid-Morning",
        "label_id": "Tengah Pagi",
        "insight_en": "professionals active during work breaks",
        "insight_id": "profesional aktif saat istirahat kerja"
    },
    {
        "window": "12:00 - 13:00",
        "label_en": "Lunch Break",
        "label_id": "Jam Makan Siang",
        "insight_en": "high engagement during midday rest",
        "insight_id": "engagement tinggi saat istirahat siang"
    },
    {
        "window": "13:00 - 17:00",
        "label_en": "Afternoon Lull",
        "label_id": "Sore Hari",
        "insight_en": "moderate activity during work hours",
        "insight_id": "aktivitas moderat selama jam kerja"
    },
    {
        "window": "17:00 - 19:00",
        "label_en": "Commute Hours",
        "label_id": "Jam Pulang Kerja",
        "insight_en": "audiences active during transit",
        "insight_id": "audiens aktif saat perjalanan pulang"
    },
    {
        "window": "19:00 - 22:00",
        "label_en": "Prime Time",
        "label_id": "Waktu Utama",
        "insight_en": "peak leisure time after dinner",
        "insight_id": "waktu santai puncak setelah makan malam"
    },
    {
        "window": "22:00 - 00:00",
        "label_en": "Late Night",
        "label_id": "Malam Hari",
        "insight_en": "night owls scrolling before sleep",
        "insight_id": "pengguna yang begadang sebelum tidur"
    },
    {
        "window": "00:00 - 06:00",
        "label_en": "Overnight",
        "label_id": "Dini Hari",
        "insight_en": "minimal but dedicated late-night audience",
        "insight_id": "audiens minimal tapi setia di larut malam"
    }
]

STYLES = [
    {
        "en": "Analytic (Focus on numbers & trends)",
        "id": "Analitik (Fokus pada angka & tren)"
    },
    {
        "en": "Strategic (Focus on ROI & Growth)",
        "id": "Strategis (Fokus pada ROI & Pertumbuhan)"
    },
    {
        "en": "Executive (Brief, Direct, Decision-oriented)",
        "id": "Eksekutif (Singkat, Langsung, Berorientasi keputusan)"
    },
    {
        "en": "Enthusiastic (High energy, Marketing tone)",
        "id": "Antusias (Energi tinggi, Nada marketing)"
    },
    {
        "en": "Advisory (Consultative, Helpful)",
        "id": "Konsultatif (Memberikan saran, Membantu)"
    },
    {
        "en": "Urgent (Creating FOMO/Action)",
        "id": "Mendesak (Menciptakan FOMO/Aksi)"
    },
    {
        "en": "Relaxed (Casual professional)",
        "id": "Santai (Profesional kasual)"
    },
    {
        "en": "Detailed (Deep dive analysis)",
        "id": "Detail (Analisis mendalam)"
    },
    {
        "en": "Persuasive (Convincing)",
        "id": "Persuasif (Meyakinkan)"
    },
    {
        "en": "Storytelling (Narrative flow)",
        "id": "Bercerita (Alur naratif)"
    }
]

# Dominance labels
DOMINANCE_LABELS = {
    "unrivaled": {"en": "Unrivaled", "id": "Tak Tertandingi"},
    "clear_lead": {"en": "Clear Lead", "id": "Unggul Jelas"},
    "tight_race": {"en": "Tight Race", "id": "Persaingan Ketat"}
}

# Graph shapes
GRAPH_SHAPES = [
    {"en": "Sharp Spike", "id": "Lonjakan Tajam"},
    {"en": "Sustained Plateau", "id": "Plateau Stabil"}
]


# --- 2. GENERATE DATASET ---
def generate_dataset():
    """Generate dataset lengkap dengan prompt sintetis dalam bahasa Indonesia."""
    dataset = []
    
    print(f"Generating {TOTAL_ROWS} skenario unik dalam bahasa Indonesia...")

    for i in range(TOTAL_ROWS):
        # Random scenario generation
        score = random.randint(70, 99)
        runner_up_score = random.randint(40, score)
        gap = score - runner_up_score
        
        # Determine dominance label
        if gap > 20:
            dominance = DOMINANCE_LABELS["unrivaled"]
        elif gap > 10:
            dominance = DOMINANCE_LABELS["clear_lead"]
        else:
            dominance = DOMINANCE_LABELS["tight_race"]
        
        # Select random elements
        graph_shape = random.choice(GRAPH_SHAPES)
        day = random.choice(DAYS)
        time_slot = random.choice(TIME_SLOTS)
        style = random.choice(STYLES)
        
        # Construct prompt untuk LLM (dalam bahasa Indonesia)
        prompt_for_llm = (
            f"Konteks Data:\n"
            f"- Hari: {day['id']}\n"
            f"- Waktu: {time_slot['window']} ({time_slot['label_id']})\n"
            f"- Skor: {score}/100 (Runner-up: {runner_up_score})\n"
            f"- Pola: Dominasi {dominance['id']} dengan perilaku "
            f"{graph_shape['id']}\n"
            f"- Perilaku Pengguna: {time_slot['insight_id']}\n"
            f"\n"
            f"Tugas: Tulis 1-2 kalimat alasan MENGAPA ini adalah waktu "
            f"terbaik untuk posting, berdasarkan sinyal data di atas.\n"
            f"Gaya Penulisan yang Diminta: {style['id']}\n"
            f"Batasi jawaban maksimal 50 kata dan spesifik tentang "
            f"pola data."
        )
        
        # Student input (versi sederhana yang akan dilihat model saat training)
        student_input = (
            f"Hari: {day['id']}, Waktu: {time_slot['window']}, "
            f"Skor: {score}, Dominasi: {dominance['id']}, "
            f"Bentuk: {graph_shape['id']}, Gaya: {style['id']}"
        )
        
        # Append to dataset
        dataset.append({
            "day_id": day['id'],
            "day_en": day['en'],
            "time": time_slot['window'],
            "score": score,
            "dominance_id": dominance['id'],
            "dominance_en": dominance['en'],
            "shape_id": graph_shape['id'],
            "shape_en": graph_shape['en'],
            "style_id": style['id'],
            "style_en": style['en'],
            "prompt_for_llm": prompt_for_llm,
            "student_input": student_input
        })
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Progress: {i + 1}/{TOTAL_ROWS} baris di-generate...")

    # Save to CSV
    df = pd.DataFrame(dataset)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print(f"\n[OK] Selesai! Membuat {OUTPUT_FILE} dengan {len(df)} baris.")
    print(f"Nama kolom: {list(df.columns)}")
    print("\nContoh baris:")
    print(f"  student_input: {df.iloc[0]['student_input']}")
    sample_prompt = df.iloc[0]['prompt_for_llm'][:250]
    print(f"  prompt_for_llm (250 karakter pertama): {sample_prompt}...")


if __name__ == "__main__":
    generate_dataset()
