# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

# ANAF API URL
ANAF_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"


class AnafLookupController(http.Controller):
    """
    Controller pentru interogarea ANAF din website
    Permite auto-completarea datelor companiei pe baza CUI-ului
    """

    @http.route(
        "/shop/anaf_lookup",
        type="json",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def anaf_lookup(self, vat=None, **kwargs):
        """
        Endpoint AJAX pentru căutarea datelor companiei în ANAF
        
        Args:
            vat (str): CUI-ul companiei (cu sau fără prefix RO)
            
        Returns:
            dict: Datele companiei sau eroare
        """
        result = {
            "success": False,
            "error": "",
            "data": {},
        }

        if not vat:
            result["error"] = "CUI-ul este obligatoriu"
            return result

        # Curăță CUI-ul
        vat = vat.strip().upper().replace(" ", "")
        
        # Elimină prefixul RO dacă există
        vat_number = vat.replace("RO", "")

        # Validare format de bază
        if not vat_number.isdigit():
            result["error"] = "CUI-ul trebuie să conțină doar cifre"
            return result

        if len(vat_number) < 2 or len(vat_number) > 10:
            result["error"] = "CUI-ul trebuie să aibă între 2 și 10 cifre"
            return result

        try:
            # Apelăm direct API-ul ANAF
            anaf_error, anaf_result = self._get_anaf_data(vat_number)

            if anaf_error:
                result["error"] = str(anaf_error)
                return result

            if not anaf_result or not anaf_result.get("date_generale"):
                result["error"] = f"Nu s-au găsit date pentru CUI-ul {vat_number}"
                return result

            # Extragem datele relevante
            general_data = anaf_result.get("date_generale", {})
            address_data = anaf_result.get("adresa_domiciliu_fiscal", {})
            vat_data = anaf_result.get("inregistrare_scop_Tva", {})

            # Construim răspunsul
            company_name = general_data.get("denumire", "").strip()
            
            # Determinăm dacă e plătitor de TVA
            is_vat_subjected = vat_data.get("scpTVA", False)
            vat_prefix = "RO" if is_vat_subjected else ""

            # Procesăm adresa
            street = ""
            if address_data.get("ddenumire_Strada"):
                street = address_data.get("ddenumire_Strada", "").strip().title()
                if address_data.get("dnumar_Strada"):
                    street += " Nr. " + address_data.get("dnumar_Strada", "").strip()

            street2 = address_data.get("ddetalii_Adresa", "").strip().title()
            
            # Procesăm orașul
            city = address_data.get("ddenumire_Localitate", "").strip()
            city = self._clean_city_name(city)

            # Procesăm județul
            state_name = address_data.get("ddenumire_Judet", "").strip()
            state_code = address_data.get("dcod_JudetAuto", "")
            
            # Căutăm ID-ul județului
            state_id = False
            if state_code:
                state = request.env["res.country.state"].sudo().search([
                    ("code", "=", state_code),
                    ("country_id.code", "=", "RO"),
                ], limit=1)
                if state:
                    state_id = state.id

            if not state_id and state_name:
                state = request.env["res.country.state"].sudo().search([
                    ("name", "ilike", state_name),
                    ("country_id.code", "=", "RO"),
                ], limit=1)
                if state:
                    state_id = state.id

            # Cod poștal
            zip_code = address_data.get("dcod_Postal", "").strip()
            
            # Telefon (dacă există)
            phone = general_data.get("telefon", "").strip()

            result["success"] = True
            result["data"] = {
                "company_name": company_name,
                "vat": vat_prefix + vat_number,
                "street": street,
                "street2": street2,
                "city": city,
                "state_id": state_id,
                "zip": zip_code,
                "phone": phone,
                "is_vat_subjected": is_vat_subjected,
                "nrc": general_data.get("nrRegCom", ""),
                "status": general_data.get("stare_inregistrare", ""),
            }

            _logger.info(
                "ANAF lookup successful for CUI %s: %s",
                vat_number,
                company_name
            )

        except Exception as e:
            _logger.error("ANAF lookup error for CUI %s: %s", vat_number, str(e))
            result["error"] = f"Eroare la interogarea ANAF: {str(e)}"

        return result

    def _get_anaf_data(self, vat_number):
        """
        Interogare directă API ANAF
        
        Args:
            vat_number (str): CUI fără prefix RO
            
        Returns:
            tuple: (error_message, result_dict)
        """
        try:
            # Pregătim datele pentru request
            today = fields.Date.to_string(fields.Date.today())
            json_data = [{"cui": int(vat_number), "data": today}]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; OdooBot/1.0)",
                "Content-Type": "application/json",
            }
            
            # Facem request-ul
            response = requests.post(
                ANAF_URL,
                json=json_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 404:
                return "CUI-ul nu a fost găsit în registrul ANAF. Verificați dacă este corect.", {}
            
            if response.status_code == 500:
                return "Serviciul ANAF este temporar indisponibil. Încercați mai târziu.", {}
            
            if response.status_code == 503:
                return "Serviciul ANAF este în mentenanță. Încercați mai târziu.", {}
                
            if response.status_code != 200:
                return f"Serviciul ANAF nu răspunde (cod {response.status_code}). Încercați mai târziu.", {}
            
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
                
                if data.get("found") and len(data["found"]) > 0:
                    return "", data["found"][0]
                elif data.get("notFound") and len(data["notFound"]) > 0:
                    return "CUI-ul nu există în baza de date ANAF. Verificați dacă l-ați introdus corect.", {}
                else:
                    return "CUI-ul nu a fost găsit. Poate fi un CUI nou, neînregistrat încă în ANAF.", {}
            else:
                return "Răspuns neașteptat de la ANAF. Încercați din nou.", {}
                
        except requests.Timeout:
            return "Conexiunea cu ANAF a expirat. Verificați conexiunea la internet și încercați din nou.", {}
        except requests.ConnectionError:
            return "Nu s-a putut conecta la ANAF. Verificați conexiunea la internet.", {}
        except requests.RequestException as e:
            return "Eroare de comunicare cu ANAF. Încercați din nou.", {}
        except ValueError:
            return "CUI invalid. Introduceți doar cifre.", {}
        except Exception as e:
            _logger.error("ANAF API unexpected error: %s", str(e))
            return "Eroare neașteptată. Încercați din nou.", {}

    def _clean_city_name(self, city):
        """
        Curăță numele orașului de prefixe comune
        """
        if not city:
            return ""
            
        city = city.upper()
        remove_prefixes = ["MUNICIPIUL", "MUN.", "MUN", "ORAȘ", "ORȘ.", "ORȘ", "JUD.", "JUD"]
        
        for prefix in remove_prefixes:
            city = city.replace(prefix, "")
        
        return city.strip().title()
