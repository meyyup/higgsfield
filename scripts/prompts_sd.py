#!/usr/bin/env python3
"""Son Damla: anahtar kare ve klip prompt'larını prompts/sd_*.txt olarak yazar.

Referanslar: assets/gorseller/sd_damla_ref.png (karakter), sd_orman_ref.png (mekân).
Kareler bu referanslarla qwen-image-3/edit ile, klipler Seedance 2.0 image-to-video ile üretilir.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "prompts"
STIL = (P / "sd_stil.txt").read_text(encoding="utf-8").strip()

DAMLA = ("Damla, the raindrop character from the reference sheet: a round classic teardrop-shaped water droplet, "
         "transparent light-blue water with a white highlight, big warm brown eyes, small eyebrows, two thin "
         "transparent arms. Keep her design exactly as in the reference")
ARKADAS = ("her two friends of the same raindrop design: Pıt, a smaller droplet, and Şıp, a bigger droplet "
           "(no clothes, no accessories)")
ORMAN = ("the pine forest clearing from the location reference: dry yellow grass, pine trees, the green "
         "recycling bin for glass on the right")
KURAL = "No people, no logos, no readable text. 16:9."

# ad: (referanslar, içerik)
KARELER = {
    "sd_k1_bulut": (["damla"],
        f"Wide shot, high in the sky on top of a big fluffy white cloud at golden hour. {DAMLA} sits on the edge "
        f"of the cloud with {ARKADAS}. Far below: a hot dry pine forest with a thin column of grey smoke rising in "
        f"the distance. Damla looks toward the camera with a worried expression, the friends peek down over the edge."),
    "sd_k2_mercek": (["orman"],
        f"Low close-up on the ground of {ORMAN}. A discarded green glass bottle lies on dry grass; the bright "
        f"sunlight passes through the glass and is focused into one tiny, intensely bright white spot on the dry "
        f"grass, with a thin curl of smoke rising from that spot. Shallow depth of field."),
    "sd_k2_alev": (["damla", "orman"],
        f"Wide shot of {ORMAN}, now on fire: orange flames spreading across the dry grass between the discarded "
        f"glass bottles, thick smoke. From the sky above, {DAMLA} and many raindrop friends dive bravely toward the "
        f"flames; where the drops hit the fire they burst into small puffs of white steam. Dramatic orange light."),
    "sd_k2_yorgun": (["damla"],
        f"Medium shot. {DAMLA} and {ARKADAS} sit exhausted and smaller than before on a charred pine branch, the "
        f"forest fire still burning in the background, orange glow and smoke. Damla is out of breath and "
        f"sad, Pıt is crying with a tear, Şıp holds Pıt."),
    "sd_k3_saganak": (["damla", "orman"],
        f"Wide shot of {ORMAN}. A heavy rain shower: thousands of raindrop characters like {DAMLA} pour down "
        f"together from a dark cloud; the last flames go out with large clouds of white steam. Blackened grass "
        f"and ash on the ground, the glass bottles still lying there."),
    "sd_k3_bulus": (["damla"],
        f"Low close-up on black ash after a fire. {DAMLA} stands next to a soot-covered green glass bottle lying "
        f"on its side; the sun shines through the bottle and makes a bright focused spot on the ash. Damla points "
        f"at the bottle with one tiny arm, eyes wide, with a sudden 'aha' realization expression."),
    "sd_k4_toplama": (["damla", "orman"],
        f"Wide shot of {ORMAN}, morning after the fire, a few green sprouts in the burnt grass. {DAMLA} leads "
        f"{ARKADAS} and many other raindrops; together they form a small sparkling stream that rolls the "
        f"discarded glass bottles across the ground toward the green recycling bin. Cheerful, busy, playful."),
    "sd_k4_kutu": (["damla", "orman"],
        f"Medium shot next to the green recycling bin for glass from the location reference. {DAMLA} and {ARKADAS} "
        f"stand on each other's shoulders like a little tower and push a green glass bottle into the round opening "
        f"of the bin. A pile of bottles is already inside. Happy proud faces, bright morning light."),
    "sd_k5_temiz": (["damla", "orman"],
        f"Wide shot of {ORMAN} on a very hot sunny summer day a year later: fresh green grass and young pine "
        f"saplings, wildflowers, no bottles anywhere, the clean area is safe. {DAMLA} relaxes happily on a big "
        f"green leaf of a bush in the foreground, sunbathing with her arms behind her head; {ARKADAS} cheer next "
        f"to her. Two small birds fly by."),
    "sd_k6_yaprak": (["damla"],
        f"Macro close-up of the tip of a green leaf in a lush summer forest, warm golden backlight. {DAMLA} hangs "
        f"at the very tip of the leaf, looking straight at the camera and winking with a big smile. Below, dark "
        f"moist soil."),
    "sd_k6_filiz": ([],
        f"Macro close-up of dark moist forest soil in warm golden light, under a green leaf. A tiny fresh green "
        f"sprout has just grown where a raindrop landed; a few sparkling water droplets glisten on it; the "
        f"leaf above is now empty."),
}

SABIT = "Keep the character design consistent. Smooth natural motion."

# ad: (başlangıç, bitiş, süre, hareket)
KLIPLER = {
    "sd_c01_bulut": ("sd_k1_bulut", None, 6,
        "The raindrops on the cloud edge peek down at the smoke far below; Damla turns to the camera and speaks "
        "with a worried face, her mouth moving. Slow gentle push-in."),
    "sd_c02_mercek": ("sd_k2_mercek", None, 5,
        "The focused sunlight spot on the dry grass grows brighter, smoke thickens, and a small flame ignites and "
        "starts to spread. Static camera."),
    "sd_c03_alev": ("sd_k2_alev", None, 5,
        "The raindrops dive into the flames and burst into puffs of steam with a hiss, but the fire keeps growing "
        "and spreading. Slow camera pull-back."),
    "sd_c04_yorgun": ("sd_k2_yorgun", None, 4,
        "Pıt cries and says something, Şıp hugs Pıt, Damla catches her breath and looks at the fire sadly. "
        "Fire flickers in the background. Static camera."),
    "sd_c05_saganak": ("sd_k3_saganak", None, 4,
        "Heavy rain of raindrop characters pours down together and the last flames die out in big clouds of white "
        "steam. Static camera."),
    "sd_c06_bulus": ("sd_k3_bulus", None, 4,
        "Damla notices the bright spot made by the sunlight through the bottle, points at it and speaks with an "
        "'aha' expression, mouth moving. Slow push-in on the bottle."),
    "sd_c07_toplama": ("sd_k4_toplama", None, 5,
        "The raindrops' little stream rolls the glass bottles across the ground toward the green recycling bin; "
        "Damla turns to the camera and speaks happily. Slow sideways tracking shot."),
    "sd_c08_kutu": ("sd_k4_kutu", None, 5,
        "The raindrop tower pushes the green bottle into the recycling bin, it drops in with a clink; the drops "
        "cheer and high-five. Static camera."),
    "sd_c09_temiz": ("sd_k5_temiz", None, 6,
        "Hot summer sun shines on the clean green clearing and nothing happens, a gentle breeze moves the grass "
        "and flowers; Damla relaxes on the leaf, Pıt jumps happily and speaks. Slow push-in."),
    "sd_c10_yaprak": ("sd_k6_yaprak", "sd_k6_filiz", 5,
        "Damla winks at the camera, lets go of the leaf tip and falls down onto the soil with a tiny splash; a "
        "small green sprout grows up from that spot. Camera tilts down with her."),
}


def main():
    for ad, (_, icerik) in KARELER.items():
        (P / f"{ad}.txt").write_text(f"{icerik} {KURAL}\n\n{STIL}\n", encoding="utf-8")
    for ad, (_, _, _, hareket) in KLIPLER.items():
        (P / f"{ad}.txt").write_text(f"{hareket} {SABIT}\n\n{STIL}\n", encoding="utf-8")
    print(f"{len(KARELER)} kare, {len(KLIPLER)} klip prompt'u yazıldı")


if __name__ == "__main__":
    main()
