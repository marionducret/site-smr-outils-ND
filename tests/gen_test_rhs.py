#!/usr/bin/env python3
"""Génère un RHS.txt synthétique (formats M1C et M1D) pour tester le convertisseur."""

def pad(s, n):
    s = str(s)
    assert len(s) <= n, f"{s!r} > {n}"
    return s.ljust(n)

def zpad(v, n):
    return str(v).zfill(n)

def base_common(fmt, finess="123456789", num_sejour="SEJ0001", semaine="032026",
                um="1000", n_das=2, n_csarr=2, n_csar=0, n_ccam=1):
    line = ""
    line += pad("", 10)                    # filler1 1-10
    line += pad(fmt, 3)                    # version_format_rhs_groupe 11-13
    line += pad(finess, 9)                 # finess 14-22
    line += pad(fmt, 3)                    # version_format_rhs 23-25
    line += pad("1234567", 7)              # sejour_ssr 26-32
    line += pad(num_sejour, 20)            # numero_sejour 33-52
    line += pad("11", 2)                   # version_classification 53-54
    line += pad("04", 2)                   # cm 55-56
    line += pad("08", 2)                   # gn 57-58
    line += pad("1", 1)                    # nr 59
    line += pad("2", 1)                    # nl 60
    line += pad("1", 1)                    # severite 61
    line += pad("000", 3)                  # code_retour 62-64
    line += pad("0", 1)                    # erreur 65
    line += pad("01012026", 8)             # date_debut_sejour 66-73
    line += pad("15022026", 8)             # date_fin_sejour 74-81
    line += pad("15061950", 8)             # date_naissance 82-89
    line += pad("1", 1)                    # sexe 90
    line += pad("63000", 5)                # code_postal 91-95
    line += pad("1", 1)                    # type_hospitalisation 96
    line += pad("01012026", 8)             # date_entree_um 97-104
    line += pad("8", 1)                    # mode_entree_um 105
    line += pad("5", 1)                    # provenance 106
    line += pad("15022026", 8)             # date_sortie_um 107-114
    line += pad("8", 1)                    # mode_sortie 115
    line += pad("0", 1)                    # destination 116
    line += pad(semaine, 6)                # semaine_annee 117-122
    line += zpad(5, 5)                     # journees_hors_we 123-127
    line += zpad(2, 2)                     # journees_we 128-129
    line += pad(um, 4)                     # numero_um 130-133
    line += pad("54B", 3)                  # type_autorisation_um 134-136
    line += pad("", 8)                     # date_intervention_chir 137-144
    line += pad("Z50800", 8)               # finalite_pec 145-152
    line += pad("I69300", 8)               # manifestation_morbide_principale 153-160
    line += pad("I63900", 8)               # affection_etiologique 161-168
    line += "2"                            # dep_habillage_toilette 169
    line += "3"                            # dep_deplacement 170
    line += "2"                            # dep_alimentation 171
    line += "1"                            # dep_continence 172
    line += "2"                            # dep_comportement 173
    line += "1"                            # dep_relation 174
    assert len(line) == 174, len(line)
    # tail
    if fmt == "M1C":
        line += zpad(n_das, 2)             # 175-176
        line += zpad(n_csarr, 3)           # 177-179
        line += zpad(n_ccam, 2)            # 180-181
        line += "1"                        # poursuite 182
        line += " "                        # filler2 183
        line += "00"                       # lisp 184-185
        line += "00"                       # type_unite_specifique 186-187
        assert len(line) == 187
    else:  # M1D
        line += zpad(n_das, 2)             # 175-176
        line += zpad(n_csarr, 3)           # 177-179
        line += zpad(n_csar, 3)            # 180-182
        line += zpad(n_ccam, 2)            # 183-184
        line += "1"                        # poursuite 185
        line += " "                        # filler2 186
        line += "00"                       # lisp 187-188
        line += "00"                       # type_unite_specifique 189-190
        assert len(line) == 190
    return line

def das_block(code):
    return pad(code, 8)

def csarr_block(code="ZCQ+188", interv="22", date="05012026"):
    b = pad(code, 7) + pad("", 3) + pad("", 2) + pad("", 2) + pad("", 2)
    b += pad(interv, 2) + pad("", 1) + zpad(1, 2) + pad(date, 8) + zpad(1, 2)
    b += zpad(1, 2) + pad("", 2)
    assert len(b) == 35, len(b)
    return b

def csar_block(code="GKQ08", interv="21", date="06012026"):
    b = pad(code, 5) + pad("", 2) + pad("02", 2) + pad("", 2) + pad("", 1)
    b += pad(interv, 2) + pad("1", 1) + pad("0", 1) + zpad(1, 2) + pad(date, 8)
    b += pad("", 2) + pad("", 2)
    assert len(b) == 30, len(b)
    return b

def ccam_block(date="07012026", code="AHQP003", ext="-00"):
    b = pad(date, 8) + pad(code, 7) + pad(ext, 3) + pad("1", 1) + pad("1", 1)
    b += pad("", 1) + zpad(1, 2)
    assert len(b) == 23, len(b)
    return b

lines = []
# Ligne 1 : M1D, 2 DAS, 2 CSARR, 1 CSAR, 1 CCAM
l = base_common("M1D", num_sejour="SEJ0001", n_das=2, n_csarr=2, n_csar=1, n_ccam=1)
l += das_block("I10") + das_block("E11900")
l += csarr_block("ZCQ+188", "22") + csarr_block("PCE+240", "27")
l += csar_block("GKQ08", "21")
l += ccam_block()
lines.append(l)
# Ligne 2 : M1D, 0 DAS, 1 CSARR, 0 CSAR, 0 CCAM, HDJ
l = base_common("M1D", num_sejour="SEJ0002", um="4000", n_das=0, n_csarr=1, n_csar=0, n_ccam=0)
l += csarr_block("NKQ+059", "70", "08012026")
lines.append(l)
# Ligne 3 : M1C, 1 DAS, 1 CSARR, 2 CCAM (dont ext PMSI '000')
l = base_common("M1C", num_sejour="SEJ0003", um="2000", n_das=1, n_csarr=1, n_ccam=2)
l += das_block("G81900")
l += csarr_block("GKR+197", "26", "09012026")
l += ccam_block("10012026", "DEQP003", "000") + ccam_block("11012026", "GLQP004", "-00")
lines.append(l)

with open("RHS_test.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"{len(lines)} lignes écrites, longueurs: {[len(l) for l in lines]}")
