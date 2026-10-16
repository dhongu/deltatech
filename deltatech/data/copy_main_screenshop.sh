# Navigați la directorul rădăcină al proiectului
cd /Users/dhongu/Odoo/odoo18/odoo-addons/deltatech

# Găsiți locația originală a imaginii (dacă nu știți exact unde se află)
find . -name "main_screenshot.png"

# Presupunând că ați găsit imaginea, să zicem în ./deltatech/static/description/main_screenshot.png
# Creați un script pentru a copia imaginea în toate modulele

for module in $(find . -type d -name "deltatech_*" -maxdepth 1); do
    # Creați directorul static/description dacă nu există
    mkdir -p "$module/static/description"

    # Copiați imaginea
    cp ./deltatech/static/description/main_screenshot.png "$module/static/description/"

    echo "Copiat în $module"
done
