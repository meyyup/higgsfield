#!/usr/bin/env bash
# ±1°C montajı: normalize → yazı katmanı → 17 parça → birleştir → yazı+altyazı → ses → son çıktı.
# Tekrar çalıştırılabilir. Konuşma kayıtları (assets/ses/ses_k1.m4a, ses_k3.m4a) yoksa
# yalnızca önizleme (work/onizleme.mp4) üretilir ve DUR mesajı verilir.
set -euo pipefail
cd "$(dirname "$0")/.."
N=work/norm; S=work/seg; A=assets/ses; O=work/overlays; LOG=out/komutlar.log
FINAL=out/TalentCup-2026_Bir_Derece_final.mp4
mkdir -p $S out
ff() { echo "ffmpeg $*" >> $LOG; ffmpeg -v error -y "$@"; }
ENC=(-c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -r 25 -an)

python3 scripts/normalize.py
[ -f $O/katman.mov ] && [ $O/katman.mov -nt scripts/overlays.py ] || python3 scripts/overlays.py

# Hayal filtresi (§3): doygunluk 0,7 + vignette + kenar bulanıklığı (maske kenarlarda beyaz)
DREAM="eq=saturation=0.7,vignette=angle=PI/5,format=gbrp,split[a][b];[b]gblur=sigma=14[bl];[1:v]format=gbrp[m];[a][bl][m]maskedmerge,format=yuv420p"

# clip ÇIKIŞ GİRİŞ başla uzunluk hedef_süre ters(0/1) hayal(0/1) donma_sn
clip() {
  local out=$1 in=$2 ss=$3 len=$4 tgt=$5 rev=$6 dream=$7 frz=${8:-0}
  local vf="trim=start=$ss:duration=$len,setpts=PTS-STARTPTS"
  [ "$rev" = 1 ] && vf="$vf,reverse"
  vf="$vf,setpts=PTS*$tgt/$len,fps=25"
  [ "$frz" != 0 ] && vf="$vf,tpad=stop_mode=clone:stop_duration=$frz"
  local n; n=$(python3 -c "print(round(($tgt+$frz)*25))")
  if [ "$dream" = 1 ]; then
    ff -i $N/$in.mp4 -loop 1 -i $O/hayal_maske.png -filter_complex "[0:v]$vf,$DREAM" -frames:v $n "${ENC[@]}" $S/$out.mp4
  else
    ff -i $N/$in.mp4 -vf "$vf" -frames:v $n "${ENC[@]}" $S/$out.mp4
  fi
}
# still ÇIKIŞ GÖRSEL süre hayal(0/1)
still() {
  local out=$1 in=$2 dur=$3 dream=$4 n; n=$(python3 -c "print(round($dur*25))")
  if [ "$dream" = 1 ]; then
    ff -loop 1 -i $N/$in.png -loop 1 -i $O/hayal_maske.png -filter_complex "[0:v]fps=25,$DREAM" -frames:v $n "${ENC[@]}" $S/$out.mp4
  else
    ff -loop 1 -i $N/$in.png -vf "fps=25,format=yuv420p" -frames:v $n "${ENC[@]}" $S/$out.mp4
  fi
}

# --- Görüntü (§4) ---------------------------------------------------------------- sn
clip  01 klip5_termostat_cevirme 0 5 5   0 0 1   #  0–6   K1 çevirme 23→24 + 1 sn donma
clip  02 klip6_gozler            0 2 2   0 0     #  6–8   K2 gözler kapanıyor
clip  03 klip1_kotu_sarma_A      0 6 5.5 0 1     #  8–13.5  2026→2040 kötü
still 04 pencere_kotu_2055       1       1       # 13.5–14.5
clip  05 klip2_kotu_sarma_B      0 6 5.5 0 1     # 14.5–20  2040→2076 kötü
clip  06 klip6_gozler            0 2 2   1 0     # 20–22  K3 gözler açılıyor
clip  07 klip5_termostat_cevirme 0 5 4.2 1 0     # 22–26.2  24→23
still 08 ela_el_22               1.8     0       # 26.2–28  22
clip  09 klip6_gozler            0 2 2   0 0     # 28–30  K4 gözler kapanıyor
clip  10 klip3_iyi_sarma_A       0 6 5.5 0 1     # 30–35.5  2026→2040 iyi
still 11 pencere_iyi_2055        1       1       # 35.5–36.5
clip  12 klip4_iyi_sarma_B       0 6 5.5 0 1     # 36.5–42  2040→2076 iyi
clip  13 klip6_gozler            0 2 2   1 0 1   # 42–45  K5 gözler açılıyor + 1 sn sessiz sabit
still 14 termostat_kis_22        4       0       # 45–49  klik → 22
still 15 termostat_yaz_25        5       0       # 49–54  yaz 25
still 16 termostat_kis_22        6       0       # 54–60  K6 kapanış + kar (katmanda)

ls $S/*.mp4 | sort | sed "s|^|file '$PWD/|;s|$|'|" > $S/liste.txt
ff -f concat -safe 0 -i $S/liste.txt -c copy work/video_ham.mp4

# --- Altyazı (§7) -----------------------------------------------------------------
cat > out/altyazi.srt <<'SRT'
1
00:00:00,500 --> 00:00:03,500
Bir derece, kimse fark etmez.

2
00:00:21,000 --> 00:00:26,000
Hiçbir şey olmamıştı. Sadece ben görmüştüm.
SRT
SUBSTYLE="FontName=Inter,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,Outline=1,Shadow=1,MarginV=14"
ff -i work/video_ham.mp4 -i $O/katman.mov -filter_complex \
  "[0:v][1:v]overlay=0:0:format=auto,subtitles=out/altyazi.srt:force_style='$SUBSTYLE',format=yuv420p" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -r 25 -an work/video_yazili.mp4

# --- Ses efektleri (kendi sentezimiz, telifsiz) ----------------------------------------
[ -f $A/tik.wav ] || ff -f lavfi -i "aevalsrc='0.9*exp(-t*260)*sin(2*PI*3100*t)+0.5*exp(-t*900)*(random(0)*2-1)':s=48000:d=0.08" -ac 2 $A/tik.wav
[ -f $A/klik.wav ] || ff -f lavfi -i "aevalsrc='exp(-t*90)*sin(2*PI*620*t)+0.7*exp(-t*40)*sin(2*PI*140*t)+0.8*exp(-t*700)*(random(0)*2-1)':s=48000:d=0.25" -ac 2 $A/klik.wav
[ -f $A/ruzgar.wav ] || ff -f lavfi -i "anoisesrc=color=brown:amplitude=0.6:d=14:seed=3" -af "lowpass=f=500,highpass=f=60,tremolo=f=0.25:d=0.6,afade=t=in:d=2,afade=t=out:st=12:d=2" -ar 48000 -ac 2 $A/ruzgar.wav
[ -f $A/muzik.mp3 ] || cp work/indirilen/478246.mp3 $A/muzik.mp3

# --- Konuşma kayıtları -----------------------------------------------------------
PREVIEW=0
for k in ses_k1 ses_k3; do
  if [ ! -f $A/$k.m4a ]; then
    PREVIEW=1; echo "DUR: $A/$k.m4a yok — kaydedilmesi gerekiyor. Sessiz yer tutucuyla önizleme üretiliyor."
    ff -f lavfi -i "anullsrc=r=48000:cl=stereo" -t 3 -c:a aac work/$k.m4a
  else cp $A/$k.m4a work/$k.m4a; fi
done

# --- Ses miksajı (§7) -------------------------------------------------------------
# müzik: A=108–122 sn → 6–20 (gerilen) · B=0–16 sn → 28–44 (yumuşak) · C=150–165 sn → 45–60 (sıcak, fade-out)
# 44–45 tam sessizlik, klik 45.0; tıkırtılar rakam değişimlerinde (1.3 · 25.1 · 26.2)
ff -i work/ses_k1.m4a -i work/ses_k3.m4a -i $A/tik.wav -i $A/klik.wav -i $A/ruzgar.wav -i $A/muzik.mp3 -filter_complex "
[0:a]aresample=48000,adelay=500:all=1[k1];
[1:a]aresample=48000,adelay=21000:all=1[k3];
[2:a]asplit=3[t1][t2][t3];
[t1]adelay=1300:all=1,volume=0.6[tk1];[t2]adelay=25100:all=1,volume=0.6[tk2];[t3]adelay=26200:all=1,volume=0.6[tk3];
[3:a]adelay=45000:all=1,volume=1.0[kl];
[4:a]volume=0.35,adelay=6000:all=1[rz];
[5:a]aresample=48000,asplit=3[ma][mb][mc];
[ma]atrim=108:122,asetpts=PTS-STARTPTS,afade=t=in:d=1,afade=t=out:st=12.8:d=1.2,adelay=6000:all=1[m1];
[mb]atrim=0:16,asetpts=PTS-STARTPTS,afade=t=in:d=1.5,afade=t=out:st=15.3:d=0.7,adelay=28000:all=1[m2];
[mc]atrim=150:165,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st=10:d=5,adelay=45000:all=1[m3];
[k1][k3][tk1][tk2][tk3][kl][rz][m1][m2][m3]amix=inputs=10:normalize=0:duration=longest,apad=whole_dur=60,atrim=0:60[mix]
" -map "[mix]" -ac 2 -ar 48000 work/ses_mix.wav

# −14 LUFS, iki geçişli loudnorm
M=$(ffmpeg -v info -i work/ses_mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
ln() { python3 -c "import json,sys;print(json.loads(sys.argv[1])['$1'])" "$M"; }
LN="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(ln input_i):measured_TP=$(ln input_tp):measured_LRA=$(ln input_lra):measured_thresh=$(ln input_thresh):offset=$(ln target_offset):linear=true"

DEST=$FINAL; [ $PREVIEW = 1 ] && DEST=work/onizleme.mp4
ff -i work/video_yazili.mp4 -i work/ses_mix.wav -map 0:v -map 1:a -af "$LN,aresample=48000" -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest $DEST

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $DEST)
python3 -c "import sys;d=float('$DUR');print(f'süre {d:.2f} sn');sys.exit(0 if 55<=d<=65 else 'DUR: süre 55–65 sn dışında')"
echo "çıktı: $DEST"
[ $PREVIEW = 1 ] && echo "DUR: konuşma kayıtları eksik — final yerine önizleme üretildi." || true
