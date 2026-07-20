#!/usr/bin/env python3
"""BetterLife — baza de date de alimente.

Fiecare aliment: key, nume, emoji, kcal la 100 g, categorie, (opțional) frozen.
Valorile calorice sunt aproximative, per 100 g (valori nutriționale uzuale).
Categorii: legume, fructe, cartofi, carne, peste, oua, lactate, cereale,
           nuci, congelate, grasimi.
"""

# key, nume, emoji, kcal/100g, categorie, frozen
_RAW = [
    # ---------------- LEGUME 🥦 ----------------
    ("rosii", "Roșii", "🍅", 18, "legume"),
    ("castraveti", "Castraveți", "🥒", 15, "legume"),
    ("morcov", "Morcov", "🥕", 41, "legume"),
    ("broccoli", "Broccoli", "🥦", 34, "legume"),
    ("salata", "Salată verde", "🥬", 15, "legume"),
    ("spanac", "Spanac", "🥬", 23, "legume"),
    ("ceapa", "Ceapă", "🧅", 40, "legume"),
    ("usturoi", "Usturoi", "🧄", 149, "legume"),
    ("vinete", "Vinete", "🍆", 25, "legume"),
    ("ardei", "Ardei gras", "🫑", 31, "legume"),
    ("dovlecel", "Dovlecel", "🥒", 17, "legume"),
    ("varza", "Varză", "🥬", 25, "legume"),
    ("ciuperci", "Ciuperci", "🍄", 22, "legume"),
    ("porumb", "Porumb", "🌽", 86, "legume"),
    ("mazare", "Mazăre", "🟢", 81, "legume"),
    ("fasole_verde", "Fasole verde", "🫛", 31, "legume"),
    ("rosii_cherry", "Roșii cherry", "🍅", 18, "legume"),
    ("telina", "Țelină", "🥬", 16, "legume"),

    # ---------------- FRUCTE 🍎 ----------------
    ("mar", "Măr", "🍎", 52, "fructe"),
    ("banana", "Banană", "🍌", 89, "fructe"),
    ("portocala", "Portocală", "🍊", 47, "fructe"),
    ("capsuni", "Căpșuni", "🍓", 32, "fructe"),
    ("struguri", "Struguri", "🍇", 69, "fructe"),
    ("pere", "Pere", "🍐", 57, "fructe"),
    ("piersici", "Piersici", "🍑", 39, "fructe"),
    ("kiwi", "Kiwi", "🥝", 61, "fructe"),
    ("ananas", "Ananas", "🍍", 50, "fructe"),
    ("pepene", "Pepene roșu", "🍉", 30, "fructe"),
    ("cirese", "Cireșe", "🍒", 63, "fructe"),
    ("afine", "Afine", "🫐", 57, "fructe"),
    ("lamaie", "Lămâie", "🍋", 29, "fructe"),
    ("mango", "Mango", "🥭", 60, "fructe"),
    ("avocado", "Avocado", "🥑", 160, "fructe"),

    # ---------------- CARTOFI 🥔 ----------------
    ("cartofi", "Cartofi", "🥔", 77, "cartofi"),
    ("cartofi_dulci", "Cartofi dulci", "🍠", 86, "cartofi"),

    # ---------------- CARNE 🍗 ----------------
    ("piept_pui", "Piept de pui", "🍗", 165, "carne"),
    ("pulpa_pui", "Pulpă de pui", "🍗", 209, "carne"),
    ("vita", "Carne de vită", "🥩", 250, "carne"),
    ("porc", "Carne de porc", "🥩", 242, "carne"),
    ("curcan", "Curcan", "🦃", 135, "carne"),
    ("sunca", "Șuncă slabă", "🥓", 145, "carne"),
    ("carnati", "Cârnați", "🌭", 300, "carne"),

    # ---------------- PEȘTE 🐟 ----------------
    ("somon", "Somon", "🐟", 208, "peste"),
    ("ton", "Ton", "🐟", 132, "peste"),
    ("cod", "Cod", "🐟", 82, "peste"),
    ("creveti", "Creveți", "🍤", 99, "peste"),
    ("macrou", "Macrou", "🐟", 205, "peste"),

    # ---------------- OUĂ 🥚 ----------------
    ("ou", "Ou", "🥚", 155, "oua"),

    # ---------------- LACTATE 🥛 ----------------
    ("lapte", "Lapte", "🥛", 42, "lactate"),
    ("iaurt_grecesc", "Iaurt grecesc", "🥛", 59, "lactate"),
    ("iaurt_slab", "Iaurt slab", "🥛", 41, "lactate"),
    ("telemea", "Brânză telemea", "🧀", 253, "lactate"),
    ("cascaval", "Cașcaval", "🧀", 350, "lactate"),
    ("branza_vaci", "Brânză de vaci", "🧀", 98, "lactate"),
    ("unt", "Unt", "🧈", 717, "lactate"),
    ("smantana", "Smântână", "🥛", 193, "lactate"),
    ("mozzarella", "Mozzarella", "🧀", 280, "lactate"),

    # ---------------- CEREALE / PÂINE / PASTE 🍞 ----------------
    ("paine", "Pâine", "🍞", 265, "cereale"),
    ("paine_integrala", "Pâine integrală", "🍞", 247, "cereale"),
    ("orez", "Orez fiert", "🍚", 130, "cereale"),
    ("paste", "Paste fierte", "🍝", 158, "cereale"),
    ("ovaz", "Fulgi de ovăz", "🌾", 389, "cereale"),
    ("mamaliga", "Mămăligă", "🌽", 85, "cereale"),
    ("cuscus", "Cuscus", "🌾", 112, "cereale"),
    ("musli", "Musli", "🥣", 375, "cereale"),

    # ---------------- NUCI / SEMINȚE 🥜 ----------------
    ("migdale", "Migdale", "🌰", 579, "nuci"),
    ("nuci", "Nuci", "🌰", 654, "nuci"),
    ("alune", "Alune", "🥜", 567, "nuci"),
    ("seminte", "Semințe floarea-soarelui", "🌻", 584, "nuci"),

    # ---------------- CONGELATE 🧊 ----------------
    ("legume_congelate", "Legume congelate (mix)", "🥗", 60, "legume", True),
    ("spanac_congelat", "Spanac congelat", "🥬", 23, "legume", True),
    ("mazare_congelata", "Mazăre congelată", "🟢", 81, "legume", True),
    ("peste_congelat", "Pește congelat", "🐟", 100, "peste", True),
    ("cartofi_prajiti", "Cartofi prăjiți congelați", "🍟", 150, "cartofi", True),
    ("pizza", "Pizza congelată", "🍕", 266, "cereale", True),
    ("nuggets", "Nuggets congelate", "🍗", 250, "carne", True),
    ("fructe_congelate", "Fructe de pădure congelate", "🫐", 50, "fructe", True),

    # ---------------- GRĂSIMI 🫒 ----------------
    ("ulei_masline", "Ulei de măsline", "🫒", 884, "grasimi"),
    ("ulei", "Ulei de floarea-soarelui", "🌻", 884, "grasimi"),
]

CATEGORIES = [
    ("legume", "Legume", "🥦"),
    ("fructe", "Fructe", "🍎"),
    ("cartofi", "Cartofi", "🥔"),
    ("carne", "Carne", "🍗"),
    ("peste", "Pește", "🐟"),
    ("oua", "Ouă", "🥚"),
    ("lactate", "Lactate", "🥛"),
    ("cereale", "Cereale & pâine", "🍞"),
    ("nuci", "Nuci & semințe", "🥜"),
    ("grasimi", "Grăsimi", "🫒"),
]

# Grame pentru o „bucată" tipică — pentru alimentele pe care le numeri (ouă, mere…).
# Cele care nu apar aici se pun doar în grame/kg.
PIECE_G = {
    "ou": 55, "mar": 180, "banana": 120, "portocala": 130, "kiwi": 75,
    "pere": 170, "piersici": 150, "ardei": 120, "ceapa": 110, "cartofi": 150,
    "cartofi_dulci": 130, "rosii": 100, "rosii_cherry": 15, "castraveti": 300,
    "lamaie": 65, "avocado": 200, "morcov": 60, "vinete": 250, "dovlecel": 200,
}

FOODS = []
for item in _RAW:
    key, name, emoji, kcal, cat = item[:5]
    frozen = item[5] if len(item) > 5 else False
    FOODS.append({"key": key, "name": name, "emoji": emoji,
                  "kcal": kcal, "cat": cat, "frozen": frozen,
                  "piece_g": PIECE_G.get(key, 0)})

BY_KEY = {f["key"]: f for f in FOODS}


def category_label(cat_key):
    for key, label, emoji in CATEGORIES:
        if key == cat_key:
            return f"{emoji} {label}"
    return cat_key
