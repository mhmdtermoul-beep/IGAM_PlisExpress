[app]

# Nom de l'application sur le téléphone
title = IGAM PlisExpress

# Nom du paquetage Android
package.name = igamplisexpress
package.domain = com.igam.plis

# Code source et extensions incluses
source.dir = .
source.include_exts = py,png,jpg,db

# Icône de l'application
icon.filename = %(source.dir)s/assets/logo.png

# Orientation (Portrait uniquement pour l'usage mobile)
orientation = portrait

# Version
version = 1.0.0

# Dépendances Python requises
requirements = python3,flet,fpdf2

# Autorisations Android (Écriture pour enregistrer les PDF)
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Ciblage Android
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1