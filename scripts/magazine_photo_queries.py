"""旅行雑誌ページで使う写真の検索語（Wikimedia Commons）。

キー:
  p:xxx            タイムラインの移動・食事など、スポットIDのない項目
  x:<ID>:<n>       特集スポットのコラージュ用の追加写真
  e:<料理名>       食べたいもの
  s:<お土産名>     お土産
選んだ写真は data/magazine-photos.json に保存される（scripts/collect-magazine-photos.py）。
"""

TIMELINE = {
    # DAY1
    "p:haneda-t3": "Haneda Airport Terminal 3 departure lobby",
    "p:haneda-checkin": "Haneda Airport international terminal check-in counters",
    "p:haneda-edo": "Haneda Airport Edo Koji",
    "p:haneda-gate": "Haneda Airport international terminal night",
    "p:af-777": "Air France Boeing 777-300ER",
    # DAY2
    "p:cdg-2e": "Charles de Gaulle Airport Terminal 2E",
    "p:alps-window": "Alps from airplane window",
    "p:vce-airport": "Aeroporto di Venezia Tessera terminal",
    "p:piazzale-roma": "Piazzale Roma Venezia",
    "p:venice-night": "Venice canal at night",
    # DAY3
    "p:cappuccino": "cappuccino cup",
    "p:venice-trattoria": "Venice restaurant",
    "p:nero-seppia": "spaghetti al nero di seppia",
    # DAY4
    "p:santa-lucia": "Venezia Santa Lucia railway station",
    "p:frecciarossa": "Frecciarossa 1000 train",
    "p:termini": "Roma Termini railway station",
    # DAY5
    "p:pizza-taglio": "pizza al taglio Rome",
    # DAY6
    "p:leonardo-express": "Leonardo Express train Fiumicino",
    "p:fco": "Fiumicino Airport Terminal 1",
    "p:vueling": "Vueling Airbus A320",
    "p:bcn-airport": "Barcelona El Prat Airport Terminal 1",
    "p:eixample": "Eixample Barcelona street building",
    "p:tapas": "tapas",
    # DAY7
    "p:bcn-metro": "Barcelona Metro station platform",
    "p:carnaval-bcn": "Carnaval Barcelona rua",
    "p:hotel-bcn": "Barcelona Eixample balcony",
    # DAY8
    "p:bcn-taxi": "Barcelona taxi",
    "p:paella": "paella marisco",
    "p:bcn-night": "Barcelona Gothic Quarter night",
    # DAY9
    "p:aerobus": "Aerobus Barcelona",
    "p:bcn-plane": "Air France Airbus A319",
    "p:cdg-t2": "Charles de Gaulle Airport Terminal 2",
    "p:paris-hotel": "Paris Haussmann building night",
    "p:monoprix": "Monoprix Paris store",
    # DAY10
    "p:paris-dawn": "Paris Opera Garnier early morning",
    "p:normandy": "Normandy countryside farmland",
    "p:omelette": "omelette Mère Poulard",
    "p:grande-rue": "Grande Rue Mont-Saint-Michel",
    "p:msm-bridge": "Mont-Saint-Michel bridge",
    "p:paris-night": "Paris boulevard night lights",
    # DAY11
    "p:tuileries": "Jardin des Tuileries",
    "p:trocadero": "Trocadéro Eiffel Tower blue hour",
    "p:paris-bistro": "Paris café terrace",
    "p:eiffel-sparkle": "Eiffel Tower illuminated night Trocadéro",
    # DAY12
    "p:falafel": "L'As du Fallafel rue des Rosiers",
    "p:rer-b": "RER B train Paris",
    "p:af-night": "Air France Boeing 777 Charles de Gaulle",
    # DAY13
    "p:af-cabin": "Air France Boeing 777 economy cabin",
    "p:haneda-arrival": "Haneda Airport Terminal 3",
    "p:tokyo-night": "Haneda airport night",
}

EXTRAS = {
    "036": ["Rialto Bridge night", "Grand Canal from Rialto Bridge"],
    "033": ["Campanile San Marco view", "Caffè Florian interior"],
    "042": ["Strada Nova Venezia", "Cannaregio canal"],
    "043": ["Rialto fish market Pescheria", "Rialto market vegetables"],
    "034": ["Basilica di San Marco mosaics interior", "Horses of Saint Mark"],
    "035": ["Doge's Palace courtyard", "Bridge of Sighs"],
    "063": ["Gondola Venice canal", "Gondolier Venice"],
    "047": ["Libreria Acqua Alta", "Acqua Alta bookshop Venice"],
    "085": ["Campo San Barnaba", "San Barnaba Venice church"],
    "016": ["Colosseum interior", "Colosseum arches"],
    "021": ["Roman Forum Arch of Septimius Severus", "Roman Forum view Capitoline"],
    "062": ["Santa Maria in Cosmedin", "Bocca della Verità"],
    "025": ["Trastevere night", "Santa Maria in Trastevere"],
    "031": ["St. Peter's Basilica interior", "Pietà Michelangelo"],
    "032": ["Sistine Chapel ceiling", "Vatican Museums Gallery of Maps"],
    "030": ["Castel Sant'Angelo Ponte Sant'Angelo", "Castel Sant'Angelo terrace view St. Peter"],
    "019": ["Pantheon Rome interior dome oculus", "Pantheon Rome night"],
    "017": ["Trevi Fountain night", "Trevi Fountain Neptune"],
    "018": ["Spanish Steps Trinità dei Monti", "Fontana della Barcaccia"],
    "008": ["La Rambla Barcelona", "Mirador de Colom"],
    "009": ["Mercat de la Boqueria stall", "La Boqueria fruit"],
    "004": ["Pont del Bisbe", "Plaça Sant Felip Neri"],
    "001": ["Sagrada Família interior", "Sagrada Família stained glass"],
    "003": ["Casa Batlló interior", "Casa Batlló roof"],
    "013": ["Passeig de Gràcia", "Panot Gaudí tile"],
    "012": ["El Nacional Barcelona", "jamón ibérico slicing"],
    "002": ["Park Güell dragon", "Park Güell bench mosaic"],
    "006": ["Casa Milà rooftop chimneys", "Casa Milà courtyard"],
    "011": ["Santa Maria del Mar Barcelona interior", "El Born Barcelona street"],
    "066": ["Palau de la Música Catalana skylight", "Palau de la Música Catalana facade"],
    "060": ["Mont-Saint-Michel low tide", "Mont-Saint-Michel night"],
    "061": ["Mont-Saint-Michel abbey cloister", "Mont-Saint-Michel abbey church"],
    "052": ["Louvre Pyramid night", "Winged Victory of Samothrace Daru staircase"],
    "051": ["Place de la Concorde fountain", "Luxor Obelisk Paris"],
    "049": ["Arc de Triomphe view from top Champs-Élysées", "Arc de Triomphe sculpture"],
    "048": ["Eiffel Tower from Trocadéro", "Eiffel Tower night"],
    "053": ["Notre-Dame de Paris interior 2024", "Notre-Dame de Paris rose window"],
    "056": ["Place des Vosges", "Rue des Rosiers Marais"],
    "054": ["Rue Montorgueil", "Passage du Grand-Cerf"],
    "090": ["Galerie Vivienne mosaic floor", "Galerie Vivienne glass roof"],
    "057": ["Galeries Lafayette dome", "Galeries Lafayette rooftop terrace"],
}

EATS = {
    "チケッティ": "cicchetti Venice",
    "スプリッツ": "Aperol Spritz",
    "オンブラ": "glass of wine bacaro Venice",
    "イカ墨のスパゲッティ": "spaghetti al nero di seppia",
    "サルデ・イン・サオール": "sarde in saor",
    "フリットゥラ・ミスタ": "fritto misto",
    "ティラミス": "tiramisu",
    "カルボナーラ": "spaghetti carbonara",
    "アマトリチャーナ": "bucatini all'amatriciana",
    "スップリ": "supplì",
    "カチョ・エ・ペペ": "cacio e pepe",
    "マリトッツォ": "maritozzo",
    "ピッツァ・アル・ターリオ": "pizza al taglio",
    "ジェラート": "gelato pistachio",
    "パン・コン・トマテ": "pa amb tomàquet",
    "パタタス・ブラバス": "patatas bravas",
    "生ハムのコーン": "jamón cone",
    "ベルムット": "vermouth Spain glass olive",
    "イベリコ生ハム": "jamón ibérico",
    "パエリア": "paella",
    "クレマ・カタラーナ": "crema catalana",
    "チュロス・コン・チョコラテ": "churros con chocolate",
    "クロケッタ": "croquetas jamón",
    "フィデウア": "fideuà",
    "ビストロの定食": "French bistro dish",
    "スーパーのお惣菜": "quiche lorraine",
    "ふわふわオムレツ": "omelette Mont-Saint-Michel",
    "ガレット＆シードル": "galette complète cidre",
    "プレ・サレの子羊": "agneau de pré-salé",
    "クロック・ムッシュ": "croque monsieur",
    "ステック・フリット": "steak frites",
    "クレープ": "crêpe Paris",
    "ファラフェル・サンド": "falafel sandwich",
    "エクレア・ババ・オ・ラム": "baba au rhum",
    "バゲット・サンド": "jambon beurre sandwich",
}

SOUVENIRS = {
    "ヴェネツィアン・マスク": "Venetian carnival masks shop",
    "ムラーノガラスの小物": "Murano glass",
    "ブラーノ島レース": "Burano lace",
    "マーブル紙のノート": "Venetian marbled paper",
    "ブッソラー（ブラーノの焼き菓子）": "Venetian biscuits",
    "古本・アート本": "Libreria Acqua Alta books",
    "ローマ古代建築の雑貨": "Rome souvenirs shop",
    "ヴィンテージ服・手工芸品": "Monti Rome shop",
    "バチカン美術館の図録・文具": "Vatican Museums shop",
    "宗教美術の小物": "rosary beads",
    "イタリアの革小物": "Italian leather goods",
    "紙もの・筆記具": "fountain pen notebook",
    "オリーブオイル・パプリカ粉": "pimentón de la Vera",
    "サフラン": "saffron spice market",
    "革小物・手作りアクセサリー": "leather wallet handmade",
    "ガウディ建築のミニチュア・マグネット": "Gaudí souvenirs",
    "トレンカディス柄の雑貨": "trencadís mosaic",
    "チョコレート": "Spanish chocolate bar",
    "カバ（スパークリングワイン）": "cava bottle",
    "モザイク柄の雑貨・トカゲグッズ": "Park Güell salamander",
    "ガウディ建築の雑貨": "Barcelona souvenir shop",
    "作家ものの雑貨・革製品": "El Born Barcelona shop",
    "イベリコ豚以外の食材": "turrón",
    "サブレ（ガレット・ブルトンヌ）": "palets bretons",
    "修道院の絵はがき・写真集": "postcards Mont-Saint-Michel",
    "塩キャラメル": "caramel au beurre salé",
    "美術館限定の雑貨・画集": "Louvre museum shop",
    "マカロン": "Ladurée macarons",
    "エッフェル塔の模型": "Eiffel Tower souvenir miniature",
    "ジャム・焼き菓子・紅茶": "Mariage Frères tea",
    "ババ・オ・ラム": "baba au rhum",
    "香水・コスメ": "perfume bottles Paris",
    "ヴィンテージ雑貨": "Village Saint-Paul antiques",
    "モノプリのエコバッグ・お菓子": "Monoprix",
}


def all_queries():
    q = dict(TIMELINE)
    for sid, terms in EXTRAS.items():
        for i, t in enumerate(terms, 1):
            q[f"x:{sid}:{i}"] = t
    q.update({f"e:{k}": v for k, v in EATS.items()})
    q.update({f"s:{k}": v for k, v in SOUVENIRS.items()})
    return q
