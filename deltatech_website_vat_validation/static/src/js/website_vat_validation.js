/** @odoo-module **/
/**
 * © 2008-2021 Deltatech
 * Dorin Hongu <dhongu(@)gmail(.)com>
 * See README.rst file on addons root folder for license details
 * 
 * Frontend validation for Romanian VAT (CUI) in website checkout
 * With ANAF auto-fill functionality
 * Follows Odoo standard JavaScript patterns and Bootstrap 5 validation
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.WebsiteVatValidation = publicWidget.Widget.extend({
    selector: '.oe_website_sale, .o_portal_details',
    events: {
        'blur #o_vat': '_onVatBlur',
        'input #o_vat': '_onVatInput',
        'change #o_country_id': '_onCountryChange',
        'blur #o_company_name': '_onCompanyNameBlur',
        'input #o_company_name': '_onCompanyNameInput',
        // Portal events
        'blur #vat': '_onVatBlur',
        'input #vat': '_onVatInput',
        'blur #company_name': '_onCompanyNameBlur',
        'input #company_name': '_onCompanyNameInput',
        'change #country_id': '_onCountryChange',
    },

    /**
     * Inițializare widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this._setupValidation();
        return this._super.apply(this, arguments);
    },

    /**
     * Configurează validarea inițială
     */
    _setupValidation: function () {
        const countrySelect = this.el.querySelector('#o_country_id') || this.el.querySelector('#country_id');
        if (countrySelect) {
            this._updateFieldsRequirement(countrySelect.value);
        }
    },

    /**
     * Event handler pentru blur pe câmpul VAT - cu ANAF lookup
     */
    _onVatBlur: async function (ev) {
        const vatInput = ev.currentTarget;
        const countrySelect = this.el.querySelector('#o_country_id') || this.el.querySelector('#country_id');
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        const countryCode = selectedOption ? selectedOption.getAttribute('code') : null;
        const vat = vatInput.value.trim();

        // Verificăm dacă arată a CUI românesc dar țara nu e România
        if (vat && this._looksLikeRomanianVat(vat) && countryCode !== 'RO') {
            this._showSelectRomaniaHint(vatInput, countrySelect);
            return;
        }

        if (countryCode === 'RO') {
            const isValid = this._validateRomanianVat(vatInput);
            
            // Dacă validarea formatului e OK, interogăm ANAF
            if (isValid && vat.length >= 2) {
                await this._lookupAnaf(vatInput);
            }
        }
        
        // Actualizează cerințele câmpurilor
        this._updateFieldsRequirement();
    },

    /**
     * Verifică dacă valoarea arată ca un CUI românesc
     */
    _looksLikeRomanianVat: function (vat) {
        if (!vat) return false;
        vat = vat.toUpperCase().trim();
        
        // Dacă începe cu RO, e clar românesc
        if (vat.startsWith('RO')) return true;
        
        // Dacă e format doar din cifre și are 2-10 caractere, probabil e CUI
        if (/^\d{2,10}$/.test(vat)) return true;
        
        return false;
    },

    /**
     * Afișează hint pentru selectarea României cu efect vizual
     */
    _showSelectRomaniaHint: function (vatInput, countrySelect) {
        this._clearValidationFeedback(vatInput);
        
        // Adaugă border albastru pentru atenție
        vatInput.classList.add('border-info');
        vatInput.classList.remove('is-invalid', 'is-valid');
        
        // Creează mesajul de hint
        const feedback = document.createElement('div');
        feedback.className = 'form-text text-info d-block o_vat_feedback o_select_romania_hint';
        feedback.innerHTML = `
            <i class="fa fa-lightbulb-o me-1"></i>
            <strong>Sugestie:</strong> Selectați <strong>România</strong> ca țară pentru auto-completare din ANAF
            <button type="button" class="btn btn-sm btn-outline-primary ms-2 o_select_romania_btn">
                <i class="fa fa-flag me-1"></i>Selectează România
            </button>
        `;
        
        // Inserează după input
        vatInput.parentNode.insertBefore(feedback, vatInput.nextSibling);
        
        // Adaugă event pe buton pentru a selecta România automat
        const selectRoBtn = feedback.querySelector('.o_select_romania_btn');
        if (selectRoBtn && countrySelect) {
            selectRoBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                
                // Găsește opțiunea România
                for (let option of countrySelect.options) {
                    if (option.getAttribute('code') === 'RO') {
                        countrySelect.value = option.value;
                        // Trigger change pentru a actualiza UI și state-urile
                        countrySelect.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        // Scroll la țară pentru vizibilitate
                        countrySelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        
                        // După selectarea țării, revalidează și fă lookup ANAF
                        setTimeout(async () => {
                            vatInput.classList.remove('border-info');
                            this._clearValidationFeedback(vatInput);
                            const isValid = this._validateRomanianVat(vatInput);
                            if (isValid && vatInput.value.trim().length >= 2) {
                                await this._lookupAnaf(vatInput);
                            }
                        }, 300);
                        
                        break;
                    }
                }
            });
        }
        
        // Highlight dropdown-ul țării
        if (countrySelect) {
            countrySelect.classList.add('border-info', 'o_country_highlight');
            // Elimină highlight-ul după 3 secunde
            setTimeout(() => {
                countrySelect.classList.remove('border-info', 'o_country_highlight');
            }, 3000);
        }
    },

    /**
     * Event handler pentru input pe câmpul VAT (validare în timp real)
     */
    _onVatInput: function (ev) {
        const vatInput = ev.currentTarget;
        const countrySelect = this.el.querySelector('#o_country_id') || this.el.querySelector('#country_id');
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        const countryCode = selectedOption ? selectedOption.getAttribute('code') : null;

        if (countryCode === 'RO') {
            // Elimină caracterele invalide în timp ce utilizatorul scrie
            let value = vatInput.value.toUpperCase();
            
            // Permite doar RO urmat de cifre sau doar cifre
            value = value.replace(/[^RO0-9]/g, '');
            
            // Dacă începe cu RO, păstrează doar o dată
            if (value.startsWith('RO')) {
                const roCount = (value.match(/RO/g) || []).length;
                if (roCount > 1) {
                    value = 'RO' + value.replace(/RO/g, '');
                }
            }
            
            vatInput.value = value;
        }
        
        // Actualizează cerințele câmpurilor
        this._updateFieldsRequirement();
    },

    /**
     * Event handler pentru schimbarea țării
     */
    _onCountryChange: function (ev) {
        const countrySelect = ev.currentTarget;
        this._updateFieldsRequirement(countrySelect.value);
        
        // Resetează mesajele de eroare existente
        const vatInput = this.el.querySelector('#o_vat') || this.el.querySelector('#vat');
        if (vatInput) {
            this._clearValidationFeedback(vatInput);
        }
    },

    /**
     * Event handler pentru blur pe câmpul Company Name
     */
    _onCompanyNameBlur: function (ev) {
        const companyInput = ev.currentTarget;
        const countrySelect = this.el.querySelector('#o_country_id') || this.el.querySelector('#country_id');
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        const countryCode = selectedOption ? selectedOption.getAttribute('code') : null;

        if (countryCode === 'RO' && companyInput.value.trim()) {
            this._validateCompanyName(companyInput);
        }
        
        // Actualizează cerințele câmpurilor
        this._updateFieldsRequirement();
    },

    /**
     * Event handler pentru input pe câmpul Company Name
     */
    _onCompanyNameInput: function (ev) {
        // Actualizează cerințele câmpurilor când utilizatorul scrie
        this._updateFieldsRequirement();
    },

    /**
     * Interogare ANAF pentru auto-completare date companie
     */
    _lookupAnaf: async function (vatInput) {
        const vat = vatInput.value.trim();
        
        if (!vat || vat.length < 2) {
            return;
        }

        // Verifică dacă CUI-ul pare valid înainte de a interoga ANAF
        const vatNumber = vat.toUpperCase().replace(/^RO/, '');
        if (vatNumber.length < 6) {
            // CUI-uri foarte scurte probabil nu există
            this._showValidationWarning(
                vatInput, 
                'CUI-ul pare incomplet. Un CUI valid are de obicei 6-10 cifre.'
            );
            return;
        }

        // Afișează indicator de loading
        this._showLoadingIndicator(vatInput);

        try {
            const result = await rpc("/shop/anaf_lookup", {
                vat: vat,
            });

            if (result.success && result.data) {
                this._fillFormWithAnafData(result.data);
                this._showValidationSuccess(vatInput, 'Date completate din ANAF ✓');
            } else if (result.error) {
                // Afișează eroarea prietenos
                this._showValidationWarning(vatInput, result.error);
            }
        } catch (error) {
            console.error('ANAF lookup error:', error);
            // Eroare de rețea sau server
            this._showValidationWarning(
                vatInput, 
                'Nu s-a putut verifica CUI-ul. Puteți continua manual.'
            );
        } finally {
            this._hideLoadingIndicator(vatInput);
        }
    },

    /**
     * Completează formularul cu datele din ANAF
     */
    _fillFormWithAnafData: function (data) {
        // Company Name
        const companyInput = this.el.querySelector('#o_company_name') || this.el.querySelector('#company_name');
        if (companyInput && data.company_name && !companyInput.value.trim()) {
            companyInput.value = data.company_name;
            this._showValidationSuccess(companyInput);
        }

        // Street
        const streetInput = this.el.querySelector('#o_street') || this.el.querySelector('#street');
        if (streetInput && data.street && !streetInput.value.trim()) {
            streetInput.value = data.street;
        }

        // Street2
        const street2Input = this.el.querySelector('#o_street2') || this.el.querySelector('#street2');
        if (street2Input && data.street2 && !street2Input.value.trim()) {
            street2Input.value = data.street2;
        }

        // City
        const cityInput = this.el.querySelector('#o_city') || this.el.querySelector('#city');
        if (cityInput && data.city && !cityInput.value.trim()) {
            cityInput.value = data.city;
        }

        // Zip Code
        const zipInput = this.el.querySelector('#o_zip') || this.el.querySelector('#zipcode');
        if (zipInput && data.zip && !zipInput.value.trim()) {
            zipInput.value = data.zip;
        }

        // State/Province
        const stateSelect = this.el.querySelector('#o_state_id') || this.el.querySelector('#state_id');
        if (stateSelect && data.state_id) {
            // Setează valoarea dacă există opțiunea
            for (let option of stateSelect.options) {
                if (parseInt(option.value) === data.state_id) {
                    stateSelect.value = option.value;
                    // Trigger change event pentru a actualiza UI-ul
                    stateSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }

        // Phone (doar dacă e gol)
        const phoneInput = this.el.querySelector('#o_phone') || this.el.querySelector('#phone');
        if (phoneInput && data.phone && !phoneInput.value.trim()) {
            phoneInput.value = data.phone;
        }
    },

    /**
     * Actualizează cerințele câmpurilor în funcție de țară și valorile existente
     * Dacă unul din câmpuri e completat, celălalt devine obligatoriu
     */
    _updateFieldsRequirement: function (countryId) {
        const countrySelect = this.el.querySelector('#o_country_id') || this.el.querySelector('#country_id');
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        const countryCode = selectedOption ? selectedOption.getAttribute('code') : null;
        
        const vatInput = this.el.querySelector('#o_vat') || this.el.querySelector('#vat');
        const companyInput = this.el.querySelector('#o_company_name') || this.el.querySelector('#company_name');
        const showVat = this.el.querySelector('#div_vat') || this.el.querySelector('[name="vat"]');

        if (countryCode === 'RO' && showVat) {
            // Pentru România, câmpurile sunt interdependente
            // Dacă unul e completat, celălalt devine obligatoriu
            const vatValue = vatInput ? vatInput.value.trim() : '';
            const companyValue = companyInput ? companyInput.value.trim() : '';

            if (vatValue && companyInput) {
                // Dacă CUI e completat, Nume Companie devine obligatoriu
                companyInput.setAttribute('required', 'required');
                this._updateLabelRequired(companyInput, true);
            } else if (companyInput) {
                companyInput.removeAttribute('required');
                this._updateLabelRequired(companyInput, false);
            }

            if (companyValue && vatInput) {
                // Dacă Nume Companie e completat, CUI devine obligatoriu
                vatInput.setAttribute('required', 'required');
                vatInput.classList.add('o_interdependent_required');
                this._updateLabelRequired(vatInput, true);
            } else if (vatInput) {
                vatInput.removeAttribute('required');
                vatInput.classList.remove('o_interdependent_required');
                this._updateLabelRequired(vatInput, false);
            }
        } else {
            // Pentru alte țări, câmpurile rămân opționale
            if (vatInput) {
                vatInput.removeAttribute('required');
                vatInput.classList.remove('o_interdependent_required');
                this._updateLabelRequired(vatInput, false);
            }
            if (companyInput) {
                companyInput.removeAttribute('required');
                this._updateLabelRequired(companyInput, false);
            }
        }
    },

    /**
     * Actualizează label-ul pentru a arăta/ascunde asteriscul de required
     */
    _updateLabelRequired: function (input, isRequired) {
        if (!input) return;
        
        // Găsește label-ul asociat
        const inputId = input.id;
        const label = this.el.querySelector(`label[for="${inputId}"]`);
        
        if (label) {
            if (isRequired) {
                label.classList.add('o_required_label');
            } else {
                label.classList.remove('o_required_label');
            }
        }
    },

    /**
     * Validează CUI-ul românesc
     */
    _validateRomanianVat: function (vatInput) {
        let vat = vatInput.value.trim().toUpperCase();
        
        // Dacă e gol și nu e obligatoriu, e valid
        if (!vat) {
            this._clearValidationFeedback(vatInput);
            return false;
        }
        
        // Elimină spațiile
        vat = vat.replace(/\s/g, '');
        
        // Verifică caractere invalide
        const invalidChars = /[-._,;:!@#$%^&*()+={}\[\]|\\<>?\/~`'"]/;
        if (invalidChars.test(vat)) {
            this._showValidationError(
                vatInput,
                'CUI-ul nu poate conține caractere speciale. Introduceți doar cifre (ex: 12345678).'
            );
            return false;
        }

        // Elimină prefixul RO dacă există
        const vatNumber = vat.replace(/^RO/, '');
        
        // Verifică dacă sunt doar cifre
        if (!/^\d+$/.test(vatNumber)) {
            this._showValidationError(
                vatInput,
                'CUI-ul trebuie să conțină doar cifre. Exemplu: 12345678'
            );
            return false;
        }

        // Verifică lungimea minimă
        if (vatNumber.length < 2) {
            this._showValidationError(
                vatInput,
                'CUI-ul este prea scurt. Trebuie să aibă minimum 2 cifre.'
            );
            return false;
        }

        // Verifică lungimea maximă
        if (vatNumber.length > 10) {
            this._showValidationError(
                vatInput,
                'CUI-ul este prea lung. Maximum 10 cifre sunt permise.'
            );
            return false;
        }

        // Verifică dacă nu începe cu 0
        if (vatNumber.startsWith('0')) {
            this._showValidationError(
                vatInput,
                'CUI-ul nu poate începe cu 0. Verificați dacă l-ați introdus corect.'
            );
            return false;
        }

        // Validare reușită - afișăm feedback pozitiv dar fără mesaj (ANAF lookup va adăuga mesajul)
        this._showValidationSuccess(vatInput);
        return true;
    },

    /**
     * Validează numele companiei
     */
    _validateCompanyName: function (companyInput) {
        const value = companyInput.value.trim();
        
        // Dacă e gol și nu e obligatoriu, e valid
        if (!value) {
            this._clearValidationFeedback(companyInput);
            return false;
        }
        
        // Verifică caractere invalide comune
        const invalidPatterns = /^[-._\s]+$/;
        if (invalidPatterns.test(value)) {
            this._showValidationError(
                companyInput,
                'Vă rugăm introduceți numele complet al companiei (ex: SC EXAMPLE SRL).'
            );
            return false;
        }

        // Verifică lungime minimă
        if (value.length < 3) {
            this._showValidationError(
                companyInput,
                'Numele companiei trebuie să aibă cel puțin 3 caractere.'
            );
            return false;
        }

        // Validare reușită
        this._showValidationSuccess(companyInput);
        return true;
    },

    /**
     * Afișează indicator de loading
     */
    _showLoadingIndicator: function (input) {
        // Adaugă clasă pentru styling
        input.classList.add('o_anaf_loading');
        
        // Creează spinner
        let spinner = input.parentNode.querySelector('.o_anaf_spinner');
        if (!spinner) {
            spinner = document.createElement('span');
            spinner.className = 'o_anaf_spinner position-absolute';
            spinner.innerHTML = '<i class="fa fa-spinner fa-spin text-muted"></i>';
            spinner.style.cssText = 'right: 10px; top: 50%; transform: translateY(-50%);';
            
            // Asigură-ne că parent-ul are position relative
            const parent = input.parentNode;
            if (getComputedStyle(parent).position === 'static') {
                parent.style.position = 'relative';
            }
            
            parent.appendChild(spinner);
        }
    },

    /**
     * Ascunde indicator de loading
     */
    _hideLoadingIndicator: function (input) {
        input.classList.remove('o_anaf_loading');
        
        const spinner = input.parentNode.querySelector('.o_anaf_spinner');
        if (spinner) {
            spinner.remove();
        }
    },

    /**
     * Afișează mesaj de eroare (Odoo standard Bootstrap 5)
     */
    _showValidationError: function (input, message) {
        this._clearValidationFeedback(input);
        
        // Adaugă clasa de eroare Bootstrap
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        
        // Creează elementul de feedback
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback d-block o_vat_feedback';
        feedback.innerHTML = '<i class="fa fa-exclamation-circle me-1"></i>' + message;
        
        // Inserează după input
        input.parentNode.insertBefore(feedback, input.nextSibling);
    },

    /**
     * Afișează mesaj de succes (Odoo standard Bootstrap 5)
     */
    _showValidationSuccess: function (input, message) {
        this._clearValidationFeedback(input);
        
        // Adaugă clasa de succes Bootstrap
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        
        // Dacă avem mesaj, afișează-l
        if (message) {
            const feedback = document.createElement('div');
            feedback.className = 'valid-feedback d-block o_vat_feedback';
            feedback.innerHTML = '<i class="fa fa-check-circle me-1"></i>' + message;
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    },

    /**
     * Afișează mesaj de avertizare (pentru erori non-critice)
     */
    _showValidationWarning: function (input, message) {
        this._clearValidationFeedback(input);
        
        // Păstrează is-valid pentru că formatul e OK
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        
        // Creează elementul de warning
        const feedback = document.createElement('div');
        feedback.className = 'form-text text-warning d-block o_vat_feedback';
        feedback.innerHTML = '<i class="fa fa-exclamation-triangle me-1"></i>' + message;
        
        input.parentNode.insertBefore(feedback, input.nextSibling);
    },

    /**
     * Elimină mesajele de validare existente
     */
    _clearValidationFeedback: function (input) {
        input.classList.remove('is-invalid', 'is-valid', 'border-info');
        
        // Elimină toate mesajele de feedback existente
        const feedbacks = input.parentNode.querySelectorAll('.o_vat_feedback, .invalid-feedback, .valid-feedback');
        feedbacks.forEach(fb => fb.remove());
    },
});

export default publicWidget.registry.WebsiteVatValidation;
