import flet as ft
# Rétrocompatibilité Flet colors
ft.colors = ft.Colors
import sqlite3
import os
from fpdf import FPDF
import datetime

# --- 1. INITIALISATION DE LA BASE DE DONNÉES LOCALE (SQLITE) ---
def init_db():
    conn = sqlite3.connect("donnees_igam.db")
    cursor = conn.cursor()
    
    # Table Profil Utilisateur (1ère installation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nom_prenom TEXT,
            email TEXT
        )
    """)
    
    # Table Consultations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT,
            zone TEXT,
            reference TEXT,
            objet TEXT,
            date_seance TEXT,
            heure_seance TEXT,
            notre_offre_ht REAL
        )
    """)
    
    # Table Plis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consultation_id INTEGER,
            nom_soumissionnaire TEXT,
            montant_ht REAL,
            delai INTEGER,
            recevabilite TEXT,
            observations TEXT,
            FOREIGN KEY (consultation_id) REFERENCES consultations (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 2. GESTION DU PROFIL UTILISATEUR ---
def get_user_profile():
    conn = sqlite3.connect("donnees_igam.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom_prenom, email FROM user_profile WHERE id = 1")
    user = cursor.fetchone()
    conn.close()
    return user

def save_user_profile(nom_prenom, email):
    conn = sqlite3.connect("donnees_igam.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_profile (id, nom_prenom, email)
        VALUES (1, ?, ?)
    """, (nom_prenom, email))
    conn.commit()
    conn.close()

# --- 3. GÉNÉRATION DU PDF AVEC SIGNATURE ---
def generer_pv_pdf(consultation_id):
    user = get_user_profile()
    nom_agent = user[0] if user else "Agent Technique"
    email_agent = user[1] if user else "non-renseigne"

    conn = sqlite3.connect("donnees_igam.db")
    cursor = conn.cursor()
    cursor.execute("SELECT client, zone, reference, objet, date_seance, heure_seance, notre_offre_ht FROM consultations WHERE id=?", (consultation_id,))
    c = cursor.fetchone()
    if not c:
        return None
    
    client, zone, ref, objet, date_s, heure_s, notre_offre = c
    cursor.execute("SELECT nom_soumissionnaire, montant_ht, delai, recevabilite, observations FROM plis WHERE consultation_id=? ORDER BY montant_ht ASC", (consultation_id,))
    plis = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    
    # En-tête officiel
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 6, f"{client.upper()} - DIRECTION REGIONALE / ZONE : {zone.upper()}", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "PROCES-VERBAL D'OUVERTURE DES PLIS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Consultation N° : {ref} | Date : {date_s} à {heure_s}", ln=True, align='C')
    pdf.cell(0, 6, f"Objet : {objet}", ln=True, align='C')
    pdf.ln(6)
    
    # Tableau comparatif
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(12, 8, "Rang", 1, 0, 'C')
    pdf.cell(60, 8, "Soumissionnaire", 1, 0, 'L')
    pdf.cell(40, 8, "Montant HT (DZD)", 1, 0, 'R')
    pdf.cell(20, 8, "Délai", 1, 0, 'C')
    pdf.cell(30, 8, "Recevabilité", 1, 0, 'C')
    pdf.cell(28, 8, "Obs.", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 8)
    for rang, pli in enumerate(plis, 1):
        nom, ht, delai, rec, obs = pli
        pdf.cell(12, 7, str(rang), 1, 0, 'C')
        pdf.cell(60, 7, str(nom)[:30], 1, 0, 'L')
        pdf.cell(40, 7, f"{ht:,.2f}", 1, 0, 'R')
        pdf.cell(20, 7, f"{delai} M", 1, 0, 'C')
        pdf.cell(30, 7, str(rec), 1, 0, 'C')
        pdf.cell(28, 7, str(obs)[:15], 1, 1, 'C')
        
    pdf.ln(12)
    
    # Bloc Traçabilité / Agent
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, f"Rapport établi par : {nom_agent} ({email_agent})", ln=True, align='L')
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, f"Généré via IGAM PlisExpress le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", ln=True, align='L')
    
    filename = f"PV_Ouverture_{ref.replace('/', '-')}_{zone}.pdf"
    pdf.output(filename)
    return filename

# --- 4. INTERFACE GRAPHIQUE FLET (IGAM PLISEXPRESS) ---
def main(page: ft.Page):
    page.title = "IGAM PlisExpress"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 12

    current_consultation_id = ft.Ref[int]()

    # Popup première installation
    txt_user_nom = ft.TextField(label="Nom & Prénom *")
    txt_user_email = ft.TextField(label="Adresse E-mail Professionnelle *")

    def valider_profil(e):
        if not txt_user_nom.value or not txt_user_email.value:
            return
        save_user_profile(txt_user_nom.value.strip(), txt_user_email.value.strip())
        dialog_profile.open = False
        page.update()

    dialog_profile = ft.AlertDialog(
        title=ft.Text("📱 Configuration Initiale IGAM"),
        content=ft.Column([
            ft.Text("Bienvenue sur IGAM PlisExpress. Renseignez votre identité pour la traçabilité des PV PDF."),
            txt_user_nom,
            txt_user_email
        ], tight=True),
        actions=[ft.ElevatedButton("Enregistrer", on_click=valider_profil)],
        modal=True
    )

    if not get_user_profile():
        page.dialog = dialog_profile
        dialog_profile.open = True

    # Formulaire Consultation
    txt_client = ft.TextField(label="Client / Organisme", value="Sonelgaz")
    txt_zone = ft.TextField(label="Zone / Direction Régionale (ex: Alger, Sétif)")
    txt_ref = ft.TextField(label="Réf. Consultation / AO")
    txt_objet = ft.TextField(label="Objet du Marché")
    txt_notre_offre = ft.TextField(label="Notre Offre HT (SNC IGAM DZD)", value="0")

    # Formulaire Pli
    txt_soum_nom = ft.TextField(label="Nom Soumissionnaire")
    txt_soum_ht = ft.TextField(label="Montant HT (DZD)")
    txt_soum_delai = ft.TextField(label="Délai (Mois)", value="5")
    dd_recevabilite = ft.Dropdown(
        label="Recevabilité",
        options=[ft.dropdown.Option("Conforme"), ft.dropdown.Option("Non Conforme")],
        value="Conforme"
    )

    liste_plis_view = ft.Column(scroll=ft.ScrollMode.AUTO)

    def rafraichir_plis():
        liste_plis_view.controls.clear()
        if current_consultation_id.current:
            conn = sqlite3.connect("donnees_igam.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nom_soumissionnaire, montant_ht, delai, recevabilite FROM plis WHERE consultation_id=? ORDER BY montant_ht ASC", (current_consultation_id.current,))
            rows = cursor.fetchall()
            conn.close()
            
            for rang, r in enumerate(rows, 1):
                liste_plis_view.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.Text(f"#{rang}", weight="bold", size=16),
                            title=ft.Text(r[0]),
                            subtitle=ft.Text(f"HT: {r[1]:,.2f} DZD | Délai: {r[2]}M | {r[3]}"),
                        )
                    )
                )
        page.update()

    def ajouter_consultation(e):
        if not txt_ref.value or not txt_zone.value:
            page.snack_bar = ft.SnackBar(ft.Text("Veuillez remplir la Zone et la Référence !"))
            page.snack_bar.open = True
            page.update()
            return

        conn = sqlite3.connect("donnees_igam.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consultations (client, zone, reference, objet, date_seance, heure_seance, notre_offre_ht)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (txt_client.value, txt_zone.value, txt_ref.value, txt_objet.value, 
              datetime.date.today().strftime("%d/%m/%Y"), "10:00", float(txt_notre_offre.value or 0)))
        
        current_consultation_id.current = cursor.lastrowid
        conn.commit()
        conn.close()

        page.snack_bar = ft.SnackBar(ft.Text("Consultation créée ! Basculez sur l'onglet Saisie."))
        page.snack_bar.open = True
        rafraichir_plis()

    def ajouter_pli(e):
        if not current_consultation_id.current:
            page.snack_bar = ft.SnackBar(ft.Text("Créez d'abord une consultation dans l'onglet 1 !"))
            page.snack_bar.open = True
            page.update()
            return

        conn = sqlite3.connect("donnees_igam.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO plis (consultation_id, nom_soumissionnaire, montant_ht, delai, recevabilite, observations)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (current_consultation_id.current, txt_soum_nom.value.upper(), float(txt_soum_ht.value or 0), 
              int(txt_soum_delai.value or 5), dd_recevabilite.value, "RAS"))
        conn.commit()
        conn.close()

        txt_soum_nom.value = ""
        txt_soum_ht.value = ""
        rafraichir_plis()

    def exporter_pdf(e):
        if current_consultation_id.current:
            pdf_path = generer_pv_pdf(current_consultation_id.current)
            page.snack_bar = ft.SnackBar(ft.Text(f"PV PDF généré : {pdf_path}"))
            page.snack_bar.open = True
            page.update()

    t1 = ft.Column([
        ft.Text("1. Préparation Consultation", size=18, weight="bold"),
        txt_client, txt_zone, txt_ref, txt_objet, txt_notre_offre,
        ft.ElevatedButton("Créer la Consultation", on_click=ajouter_consultation, bgcolor=ft.colors.BLUE_900, color="white")
    ], scroll=ft.ScrollMode.AUTO)

    t2 = ft.Column([
        ft.Text("2. Saisie Pli en Séance", size=18, weight="bold"),
        txt_soum_nom, txt_soum_ht, txt_soum_delai, dd_recevabilite,
        ft.ElevatedButton("➕ Valider le Pli", on_click=ajouter_pli, bgcolor=ft.colors.GREEN_700, color="white"),
        ft.Divider(),
        ft.Text("Classement Provisoire", size=16, weight="bold"),
        liste_plis_view
    ], scroll=ft.ScrollMode.AUTO)

    t3 = ft.Column([
        ft.Text("3. Clôture & Rapport", size=18, weight="bold"),
        ft.ElevatedButton("📄 Générer le PV PDF Officiel", on_click=exporter_pdf, bgcolor=ft.colors.RED_700, color="white")
    ])

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(label="Préparation", content=t1),
            ft.Tab(label="Saisie Pli", content=t2),
            ft.Tab(label="Rapport PDF", content=t3),
        ],
        expand=True
    )

    page.add(tabs)

ft.app(target=main)
