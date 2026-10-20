#!/usr/bin/env python3
"""v2 çekim planının prompt'larını prompts/v2_*.txt olarak yazar.

v2 kuralı: Ela her karede aynı orta planda, termostat ile pencerenin arasında.
Tüm kareler ana kareden (v2_ana_kadraj) "yalnızca şunu değiştir" düzenlemesiyle üretilir;
klipler bu karelerin başlangıç/bitiş zinciriyle bağlanır, sert kesme olmaz.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "prompts"
STIL = (P / "stil.txt").read_text(encoding="utf-8").strip()

ELA = ("Ela: a 12-year-old girl with shoulder-length wavy chestnut-brown hair, a soft round childlike face "
       "with light freckles, big warm brown eyes, wearing a chunky mustard-yellow knit sweater")

KADRAJ = (
    "Medium shot, locked-off static camera, eye level, straight-on view of a plain warm-grey hallway wall. "
    "On the left part of the wall, at the girl's shoulder height: a round unbranded wall thermostat with a brushed "
    "metal bezel and a black display showing one large white number. On the right half of the same wall: a large "
    "window with a white frame. Through the window: a gentle hill with a single tree on it, and the sea in the "
    "distance. Standing in front of the wall between the thermostat and the window: " + ELA + ". She is seen from "
    "the waist up in three-quarter view, body turned slightly toward the window, her whole face clearly visible "
    "and well lit. No logos, no text other than the thermostat number. 16:9."
)

EDIT = (
    "Edit the reference image. Keep the camera, framing, wall, the round thermostat (size, position, brushed metal "
    "bezel, black display, white digit font), the window frame, and the girl (same face, same age, same hair, same "
    "mustard-yellow sweater, same position) exactly identical. Change only what is described below."
)

# ad: (tür, içerik)
GORSELLER = {
    "v2_ana_kadraj": ("t2i",
        "Winter night. The thermostat display shows \"23\". Through the window: a bare leafless tree on the hill, "
        "no snow anywhere, the sea far away under a dark blue night sky. The hallway is dim and chilly; cold blue "
        "moonlight comes through the window and a soft warm lamp light from the left lights her face. Ela hugs "
        "herself with her arms, shoulders raised, shivering from the cold, looking at the thermostat with a small "
        "pout."),
    "v2_k1_24": ("edit",
        "The thermostat display now shows \"24\". Ela's right index finger rests on the thermostat dial; she has a "
        "small satisfied, slightly guilty smile."),
    "v2_k1_bakis": ("edit",
        "The thermostat display shows \"24\". Ela has turned her head toward the window and looks out at the hill "
        "with a curious, slightly puzzled frown, her hand lowered."),
    "v2_kapali_24": ("edit",
        "The thermostat display shows \"24\". Ela's eyes are gently closed, face toward the window, calm and "
        "concentrating, as if imagining something."),
    "v2_kotu_2040": ("edit",
        "The thermostat display shows \"24\". Through the window the tree on the hill is dead, grey and leafless "
        "with broken branches; the hill is dry brown cracked earth; the sky is a pale dusty yellow. Ela's eyes are "
        "closed, her eyebrows drawn together in worry; warmer yellowish light falls on her face."),
    "v2_kotu_2055": ("edit",
        "The thermostat display shows \"24\". Through the window the sea has risen high: grey flood water covers "
        "the bottom of the hill and the street, only the dead tree trunk sticks out of the water; heavy grey-orange "
        "sky. Ela's eyes are tightly closed, her face tense and frightened, lips pressed together; orange light on "
        "her face."),
    "v2_kotu_2076": ("edit",
        "The thermostat display shows \"24\". Through the window: a burning orange sky full of smoke haze, the hill "
        "is bare cracked desert, no tree at all, the empty flooded street below, the window glass is slightly fogged. "
        "Ela's eyes are squeezed shut, she looks scared and sad, a tear on her cheek; strong orange light on her "
        "face."),
    "v2_uyanis_24": ("edit",
        "The thermostat display shows \"24\". Through the window everything is back to the present winter night: "
        "bare tree on the hill, no snow, the sea, dark blue sky. Ela's eyes are wide open in shock, mouth slightly "
        "open, staring at the window."),
    "v2_karar_22": ("edit",
        "The thermostat display now shows \"22\". Through the window the present winter night: bare tree, dark blue "
        "sky, the sea. Ela's index finger is on the thermostat dial; her face is determined and serious, chin up."),
    "v2_kapali_22": ("edit",
        "The thermostat display shows \"22\". Through the window the present winter night. Ela's eyes are gently "
        "closed, face toward the window, with a hopeful soft expression."),
    "v2_iyi_2040": ("edit",
        "The thermostat display shows \"22\". Through the window: early morning, white snow covers the hill, the "
        "tree on the hill has grown bigger and healthy, the sea calm and blue in the distance. Ela's eyes are "
        "closed and she has a small peaceful smile; soft light on her face."),
    "v2_iyi_2055": ("edit",
        "The thermostat display shows \"22\". Through the window: a bright spring day, the tree on the hill is now "
        "big with a full green crown, its long shadow reaching toward the window, fresh green grass, the sea in its "
        "place, clear blue sky. Ela's eyes are closed and she smiles warmly; soft sunlight on her face."),
    "v2_iyi_2076": ("edit",
        "The thermostat display shows \"22\". Through the window: a huge old green tree on the hill under a clear "
        "blue sky, the sea sparkling in the distance; under the tree stands an elderly woman with grey hair and a "
        "mustard-yellow scarf, looking toward the window and smiling. Ela's eyes are closed and she is smiling "
        "happily; warm golden light on her face."),
    "v2_mutlu_22": ("edit",
        "The thermostat display shows \"22\". Through the window the present winter night, bare tree, the sea. "
        "Ela's eyes are open, she smiles warmly and confidently, her index finger pressing the center of the "
        "thermostat; she now wears a cosy knitted mustard-yellow cardigan over her sweater."),
    "v2_yaz_24": ("edit",
        "Summer daytime. Bright warm daylight fills the hallway. The thermostat display is blue and shows a large "
        "white \"24\". Through the window: green summer hill, the tree full of leaves, blue sea, blue sky. Ela wears "
        "a short-sleeved mustard-yellow t-shirt instead of the sweater, her finger on the thermostat dial, relaxed."),
    "v2_yaz_25": ("edit",
        "Summer daytime. Bright warm daylight fills the hallway. The thermostat display is blue and shows a large "
        "white \"25\". Through the window: green summer hill, the tree full of leaves, blue sea, blue sky. Ela wears "
        "a short-sleeved mustard-yellow t-shirt, she has just turned the dial, and she winks at the camera with a "
        "knowing smile."),
    "v2_kar_22": ("edit",
        "Winter night. The thermostat display shows \"22\". Through the window: big soft snowflakes are falling, "
        "the hill and the tree branches are covered with fresh white snow, warm cosy light in the hallway. Ela, in "
        "the mustard-yellow cardigan over her sweater, looks out of the window with a happy, peaceful smile, her "
        "hands holding the cardigan closed."),
}

SABIT = ("Camera completely static, no zoom, no camera shake. The wall, the window frame and the thermostat do not "
         "move. The girl keeps the same face and clothes.")

# ad: (başlangıç, bitiş, süre, hareket)
KLIPLER = {
    "v2_klip01_cevirme": ("v2_ana_kadraj", "v2_k1_24", 5,
        "The cold girl unfolds her arms, reaches out and turns the thermostat dial clockwise with her index finger; "
        "the display number changes from 23 to 24; she smiles a little."),
    "v2_klip02_bakis": ("v2_k1_24", "v2_kapali_24", 5,
        "The girl lowers her hand, notices something through the window, turns her head toward it with a curious "
        "frown, then slowly closes her eyes."),
    "v2_klip03_kotu_A": ("v2_kapali_24", "v2_kotu_2040", 5,
        "Time passes quickly outside the window: the tree dries out and dies, the hill turns brown and cracks. The "
        "girl keeps her eyes closed and frowns with worry. Thermostat number stays 24."),
    "v2_klip04_kotu_B": ("v2_kotu_2040", "v2_kotu_2055", 4,
        "Outside the window the sea rises and floods the street and the foot of the hill. The girl, eyes closed, "
        "looks frightened. Thermostat number stays 24."),
    "v2_klip05_kotu_C": ("v2_kotu_2055", "v2_kotu_2076", 4,
        "Outside the window the sky turns burning orange with smoke, the dead tree disappears. The girl squeezes "
        "her eyes shut, scared, a tear rolls down. Thermostat number stays 24."),
    "v2_klip06_uyanis": ("v2_uyanis_24", "v2_karar_22", 5,
        "The girl, wide-eyed and shocked, takes a breath, becomes determined, reaches to the thermostat and turns "
        "the dial counter-clockwise two steps; the number changes from 24 to 23 to 22."),
    "v2_klip07_iyi_A": ("v2_kapali_22", "v2_iyi_2040", 5,
        "Time passes outside the window: snow falls and covers the hill, the tree grows stronger. The girl, eyes "
        "closed, begins to smile. Thermostat number stays 22."),
    "v2_klip08_iyi_B": ("v2_iyi_2040", "v2_iyi_2055", 4,
        "Outside the window the snow melts into spring, the tree grows a full green crown, its shadow reaches the "
        "window. The girl smiles warmly, eyes closed. Thermostat number stays 22."),
    "v2_klip09_iyi_C": ("v2_iyi_2055", "v2_iyi_2076", 4,
        "Outside the window the tree grows huge and old, an elderly woman walks under it and looks toward the "
        "window. The girl smiles happily, eyes closed. Thermostat number stays 22."),
    "v2_klip10_klik": ("v2_karar_22", "v2_mutlu_22", 5,
        "The girl opens her eyes, smiles confidently, presses the center of the thermostat once firmly, then pulls "
        "a mustard-yellow cardigan around her shoulders."),
    "v2_klip11_yaz": ("v2_yaz_24", "v2_yaz_25", 4,
        "On a bright summer day, the girl turns the blue thermostat dial one step clockwise; the number changes "
        "from 24 to 25; she winks at the camera with a knowing smile."),
    "v2_klip12_kar": ("v2_mutlu_22", "v2_kar_22", 5,
        "Big soft snowflakes begin to fall outside the window and cover the hill and the tree. The girl looks out "
        "and smiles peacefully."),
}


def main():
    for ad, (tur, icerik) in GORSELLER.items():
        bas = KADRAJ if tur == "t2i" else KADRAJ + "\n\n" + EDIT
        (P / f"{ad}.txt").write_text(f"{bas}\n\n{icerik}\n\n{STIL}\n", encoding="utf-8")
    for ad, (_, _, _, hareket) in KLIPLER.items():
        (P / f"{ad}.txt").write_text(f"{hareket} {SABIT}\n\n{STIL}\n", encoding="utf-8")
    print(f"{len(GORSELLER)} görsel, {len(KLIPLER)} klip prompt'u yazıldı")


if __name__ == "__main__":
    main()
