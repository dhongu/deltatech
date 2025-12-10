/** @odoo-module **/
/**
 * 2008-2021 Deltatech
 * Dorin Hongu <dhongu(@)gmail(.)com>
 * Vezi fisierul README.rst din radacina addon-ului pentru detalii despre licenta
 *
 * Validare frontend pentru CUI romanesc in checkout-ul Odoo.
 * Include completarea automata a datelor din ANAF.
 * Respecta pattern-urile standard Odoo si validarea Bootstrap 5.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";

const DUPLICATE_HINT_CLASS = "o_duplicate_hint";
const DUPLICATE_GLOBAL_MARKER = "o_duplicate_global_cta";
const DUPLICATE_SUMMARY_CLASS = "o_duplicate_summary";

publicWidget.registry.WebsiteVatValidation = publicWidget.Widget.extend({
    selector: ".oe_website_sale, .o_portal_details",
    events: {
        "blur #o_vat": "_onVatBlur",
        "input #o_vat": "_onVatInput",
        "change #o_country_id": "_onCountryChange",
        "change #o_invoice_company": "_onInvoiceCompanyToggle",
        "blur #o_company_name": "_onCompanyNameBlur",
        "input #o_company_name": "_onCompanyNameInput",
        // Evenimente dedicate formularului de portal
        "blur #vat": "_onVatBlur",
        "input #vat": "_onVatInput",
        "blur #company_name": "_onCompanyNameBlur",
        "input #company_name": "_onCompanyNameInput",
        "change #country_id": "_onCountryChange",
        'blur input[name="email"]': "_onEmailBlur",
        'input input[name="email"]': "_onEmailInput",
        'blur input[name="phone"]': "_onPhoneBlur",
        'input input[name="phone"]': "_onPhoneInput",
        "click .o_duplicate_send_link": "_onSendAccessLink",
        "click .o_duplicate_global_send_link": "_onSendAccessLink",
    },

    /**
     * Initializare widget.
     */
    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._setupValidation();
            this._injectGlobalDuplicateCTA();
            // În caz că alerta se randărează cu întârziere, mai încercăm o dată după un scurt delay
            setTimeout(() => this._injectGlobalDuplicateCTA(), 200);
            this._observeAlerts();
        });
    },

    /**
     * Configureaza validarea initiala.
     */
    _setupValidation: function () {
        const countrySelect = this._getCountrySelect();
        if (countrySelect) {
            this._updateFieldsRequirement();
        }

        // Ne asiguram ca starea initiala a sectiunii corespunde butonului de comutare
        const invoiceCheckbox = this.el.querySelector("#o_invoice_company");
        const companySections = this.el.querySelectorAll("#o_company_section_collapse, .o-company-collapse");
        if (companySections.length && invoiceCheckbox) {
            this._setCompanySectionVisibility(invoiceCheckbox.checked);
            companySections.forEach((section) => {
                section.addEventListener("shown.bs.collapse", () => this._updateFieldsRequirement());
                section.addEventListener("hidden.bs.collapse", () => this._updateFieldsRequirement());
            });
        }

        this._initTooltips();
    },

    /**
     * Initializam tooltips pe baza Bootstrap 5.
     */
    _initTooltips: function () {
        const tooltipElements = this.el.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach((el) => {
            if (window.bootstrap && window.bootstrap.Tooltip) {
                new window.bootstrap.Tooltip(el);
            }
        });

        // Ștergem eventualele hint-uri vechi de duplicate
        this._clearDuplicateHints();
    },

    /**
     * Afiseaza sau ascunde sectiunea companiei si sincronizeaza starea comutatorului.
     */
    _setCompanySectionVisibility: function (shouldShow) {
        const invoiceCheckbox = this.el.querySelector("#o_invoice_company");
        const companySections = this.el.querySelectorAll("#o_company_section_collapse, .o-company-collapse");
        companySections.forEach((section) => {
            section.classList.toggle("show", shouldShow);
        });
        if (invoiceCheckbox) {
            invoiceCheckbox.setAttribute("aria-expanded", shouldShow ? "true" : "false");
            invoiceCheckbox.checked = shouldShow;
        }
    },

    /**
     * Gaseste selectul pentru tara (functioneaza atat in checkout, cat si in portal).
     */
    _getCountrySelect: function () {
        return (
            this.el.querySelector("#o_country_id") ||
            this.el.querySelector("#country_id") ||
            this.el.querySelector('select[name="country_id"]')
        );
    },

    /**
     * Gaseste input-ul pentru CUI.
     */
    _getVatInput: function () {
        return (
            this.el.querySelector("#o_vat") ||
            this.el.querySelector("#vat") ||
            this.el.querySelector('input[name="vat"]')
        );
    },

    /**
     * Gaseste input-ul pentru email.
     */
    _getEmailInput: function () {
        return this.el.querySelector("#email") || this.el.querySelector('input[name="email"]');
    },

    /**
     * Gaseste input-ul pentru telefon.
     */
    _getPhoneInput: function () {
        return this.el.querySelector("#phone") || this.el.querySelector('input[name="phone"]');
    },

    /**
     * Gaseste input-ul pentru numele companiei.
     */
    _getCompanyInput: function () {
        return (
            this.el.querySelector("#o_company_name") ||
            this.el.querySelector("#company_name") ||
            this.el.querySelector('input[name="company_name"]')
        );
    },

    /**
     * Rutina pentru evenimentul blur pe campul VAT - cu ANAF lookup.
     */
    _onVatBlur: async function (ev) {
        const vatInput = ev.currentTarget;
        const vat = vatInput.value;
        this._clearDuplicateHints();
        const countrySelect = this._getCountrySelect();
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        let countryCode = selectedOption ? selectedOption.getAttribute("code") : null;
        if (!countryCode && selectedOption && this._matchesRomaniaLabel(selectedOption.text)) {
            countryCode = "RO";
        }

        // Verificam daca arata ca un CUI romanesc dar tara nu este Romania
        if (vat && this._looksLikeRomanianVat(vat) && countryCode !== "RO") {
            this._showSelectRomaniaHint(vatInput, countrySelect);
            return;
        }

        if (countryCode === "RO") {
            const isValid = this._validateRomanianVat(vatInput);
            if (isValid && vat.length >= 2) {
                await this._lookupAnaf(vatInput);
            }
        }

        this._updateFieldsRequirement();
    },

    /**
     * Verifica daca valoarea arata ca un CUI romanesc.
     */
    _looksLikeRomanianVat: function (vat) {
        if (!vat) return false;
        const normalizedVat = vat.toUpperCase().trim();
        if (normalizedVat.startsWith("RO")) return true;
        if (/^\d{2,10}$/.test(normalizedVat)) return true;
        return false;
    },

    /**
     * Normalizeaza textul tarii pentru a identifica Romania indiferent de diacritice.
     */
    _matchesRomaniaLabel: function (label) {
        if (!label) {
            return false;
        }
        let normalized = label.toLowerCase();
        if (typeof normalized.normalize === "function") {
            normalized = normalized.normalize("NFD");
        }
        normalized = normalized.replace(/[\u0300-\u036f]/g, "");
        return normalized.includes("romania");
    },

    /**
     * Afiseaza hint pentru selectarea Romaniei cu efect vizual.
     */
    _showSelectRomaniaHint: function (vatInput, countrySelect) {
        this._clearValidationFeedback(vatInput);

        vatInput.classList.add("border-info");
        vatInput.classList.remove("is-invalid", "is-valid");

        const feedback = document.createElement("div");
        feedback.className = "form-text text-info d-block o_vat_feedback o_select_romania_hint";
        feedback.innerHTML = `
            <i class="fa fa-lightbulb-o me-1"></i>
            <strong>${_t("Hint")}:</strong> ${_t("Select")} <strong>${_t("Romania")}</strong> ${_t(
            "as your country for ANAF auto-fill"
        )}
            <button type="button" class="btn btn-sm btn-outline-primary ms-2 o_select_romania_btn">
                <i class="fa fa-flag me-1"></i>${_t("Select Romania")}
            </button>
        `;

        vatInput.parentNode.insertBefore(feedback, vatInput.nextSibling);

        const selectRoBtn = feedback.querySelector(".o_select_romania_btn");
        if (selectRoBtn && countrySelect) {
            selectRoBtn.addEventListener("click", async (e) => {
                e.preventDefault();

                for (const option of countrySelect.options) {
                    const code = option.getAttribute("code");
                    const text = option.text.toLowerCase();
                    if (code === "RO" || text.includes("romania")) {
                        countrySelect.value = option.value;
                        countrySelect.dispatchEvent(new Event("change", {bubbles: true}));
                        countrySelect.scrollIntoView({behavior: "smooth", block: "center"});

                        setTimeout(async () => {
                            vatInput.classList.remove("border-info");
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

        if (countrySelect) {
            countrySelect.classList.add("border-info", "o_country_highlight");
            setTimeout(() => {
                countrySelect.classList.remove("border-info", "o_country_highlight");
            }, 3000);
        }
    },

    /**
     * Rutina pentru evenimentul input pe campul VAT (validare in timp real).
     */
    _onVatInput: function (ev) {
        const vatInput = ev.currentTarget;
        const countrySelect = this._getCountrySelect();
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        let countryCode = selectedOption ? selectedOption.getAttribute("code") : null;
        if (!countryCode && selectedOption && this._matchesRomaniaLabel(selectedOption.text)) {
            countryCode = "RO";
        }

        // Eliminam caracterele invalide in timp ce utilizatorul scrie
        let value = vatInput.value.toUpperCase();
        value = value.replace(/[^RO0-9]/g, "");

        // Daca incepe cu RO, pastram doar o aparitie
        if (value.startsWith("RO")) {
            const roCount = (value.match(/RO/g) || []).length;
            if (roCount > 1) {
                value = "RO" + value.replace(/RO/g, "");
            }
        }

        vatInput.value = value;

        this._updateFieldsRequirement();
    },

    /**
     * Rutina pentru evenimentul schimbarea tarii.
     */
    _onCountryChange: function () {
        this._updateFieldsRequirement();

        const vatInput = this._getVatInput();
        if (vatInput) {
            this._clearValidationFeedback(vatInput);
        }
    },

    /**
     * Schimba vizibilitatea sectiunii companiei si cerintele asociate.
     */
    _onInvoiceCompanyToggle: function (ev) {
        this._setCompanySectionVisibility(ev.currentTarget.checked);
        this._updateFieldsRequirement();
    },

    /**
     * Rutina pentru evenimentul blur pe campul Company Name.
     */
    _onCompanyNameBlur: function (ev) {
        const companyInput = ev.currentTarget;
        this._validateCompanyName(companyInput);
        this._updateFieldsRequirement();
    },

    /**
     * Rutina pentru evenimentul input pe campul Company Name.
     */
    _onCompanyNameInput: function () {
        this._updateFieldsRequirement();
    },

    /**
     * Rutina pentru evenimentul blur pe email.
     */
    _onEmailBlur: function () {
        const emailInput = this._getEmailInput();
        if (emailInput) {
            this._clearDuplicateHints();
            this._validateEmail(emailInput);
        }
    },

    /**
     * Rutina pentru evenimentul input pe email.
     */
    _onEmailInput: function () {
        const emailInput = this._getEmailInput();
        if (emailInput) {
            this._clearValidationFeedback(emailInput);
        }
    },

    /**
     * Rutina pentru evenimentul blur pe telefon.
     */
    _onPhoneBlur: function () {
        const phoneInput = this._getPhoneInput();
        const countrySelect = this._getCountrySelect();
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        let countryCode = selectedOption ? selectedOption.getAttribute("code") : null;
        if (!countryCode && selectedOption && this._matchesRomaniaLabel(selectedOption.text)) {
            countryCode = "RO";
        }
        this._clearDuplicateHints();
        this._validatePhone(phoneInput, countryCode);
    },

    /**
     * Rutina pentru evenimentul input pe telefon.
     */
    _onPhoneInput: function () {
        const phoneInput = this._getPhoneInput();
        if (phoneInput) {
            this._clearValidationFeedback(phoneInput);
        }
    },

    /**
     * Interogare ANAF pentru auto-completare date companie.
     */
    _lookupAnaf: async function (vatInput) {
        const vat = vatInput.value.trim();
        if (!vat || vat.length < 2) {
            return;
        }

        const vatNumber = vat.toUpperCase().replace(/^RO/, "");
        if (vatNumber.length < 6) {
            this._showValidationWarning(
                vatInput,
                _t("The VAT number seems incomplete. A valid number usually has 6-10 digits.")
            );
            return;
        }

        this._showLoadingIndicator(vatInput);

        try {
            const result = await rpc("/shop/anaf_lookup", {
                vat: vat,
            });

            if (result.success && result.data) {
                this._fillFormWithAnafData(result.data);
                this._showValidationSuccess(vatInput, _t("Data retrieved from ANAF."));
                this._markAnafStatus(true, vatInput, result.data.vat || vat);
            } else if (result.error) {
                this._showValidationWarning(vatInput, result.error);
                this._markAnafStatus(false, vatInput);
            }
        } catch (error) {
            console.error("ANAF lookup error:", error);
            // Daca interogarea ANAF esueaza, afisam un mesaj bland si lasam utilizatorul sa continue manual
            this._showValidationWarning(vatInput, _t("Couldn't verify the VAT number. You can continue manually."));
            this._markAnafStatus(false, vatInput);
        } finally {
            this._hideLoadingIndicator(vatInput);
        }
    },

    /**
     * Completeaza formularul cu datele din ANAF.
     */
    _fillFormWithAnafData: function (data) {
        const companyInput = this._getCompanyInput();
        if (companyInput && data.company_name && !companyInput.value.trim()) {
            companyInput.value = data.company_name;
            this._showValidationSuccess(companyInput);
        }

        const streetInput =
            this.el.querySelector("#o_street") ||
            this.el.querySelector("#street") ||
            this.el.querySelector('[name="street"]');
        if (streetInput && data.street && !streetInput.value.trim()) {
            streetInput.value = data.street;
        }

        const street2Input =
            this.el.querySelector("#o_street2") ||
            this.el.querySelector("#street2") ||
            this.el.querySelector('[name="street2"]');
        if (street2Input && data.street2 && !street2Input.value.trim()) {
            street2Input.value = data.street2;
        }

        const cityInput =
            this.el.querySelector("#o_city") ||
            this.el.querySelector("#city") ||
            this.el.querySelector('[name="city"]');
        if (cityInput && data.city && !cityInput.value.trim()) {
            cityInput.value = data.city;
        }

        const zipInput =
            this.el.querySelector("#o_zip") ||
            this.el.querySelector("#zipcode") ||
            this.el.querySelector('[name="zipcode"]');
        if (zipInput && data.zip && !zipInput.value.trim()) {
            zipInput.value = data.zip;
        }

        const stateSelect =
            this.el.querySelector("#o_state_id") ||
            this.el.querySelector("#state_id") ||
            this.el.querySelector('[name="state_id"]');
        if (stateSelect && data.state_id) {
            for (const option of stateSelect.options) {
                if (parseInt(option.value, 10) === data.state_id) {
                    stateSelect.value = option.value;
                    stateSelect.dispatchEvent(new Event("change", {bubbles: true}));
                    break;
                }
            }
        }

        const phoneInput =
            this.el.querySelector("#o_phone") ||
            this.el.querySelector("#phone") ||
            this.el.querySelector('[name="phone"]');
        if (phoneInput && data.phone && !phoneInput.value.trim()) {
            phoneInput.value = data.phone;
        }
    },

    /**
     * Actualizeaza cerintele campurilor in functie de tara si valorile existente.
     * Daca unul din campuri este completat, celalalt devine obligatoriu.
     */
    _updateFieldsRequirement: function () {
        const countrySelect = this._getCountrySelect();
        const selectedOption = countrySelect ? countrySelect.options[countrySelect.selectedIndex] : null;
        let countryCode = selectedOption ? selectedOption.getAttribute("code") : null;
        if (!countryCode && selectedOption && this._matchesRomaniaLabel(selectedOption.text)) {
            countryCode = "RO";
        }

        const vatInput = this._getVatInput();
        const companyInput = this._getCompanyInput();
        const invoiceCheckbox = this.el.querySelector("#o_invoice_company");
        const companySections = this.el.querySelectorAll("#o_company_section_collapse, .o-company-collapse");

        const sectionVisible = companySections.length
            ? Array.from(companySections).some(
                  (section) => section.classList.contains("show") || section.classList.contains("collapsing")
              )
            : invoiceCheckbox
            ? invoiceCheckbox.checked
            : true;

        if (!sectionVisible) {
            if (vatInput) {
                vatInput.removeAttribute("required");
                vatInput.classList.remove("o_interdependent_required");
                this._updateLabelRequired(vatInput, false);
            }
            if (companyInput) {
                companyInput.removeAttribute("required");
                this._updateLabelRequired(companyInput, false);
            }
            return;
        }

        if (countryCode === "RO") {
            const vatValue = vatInput ? vatInput.value.trim() : "";
            const companyValue = companyInput ? companyInput.value.trim() : "";

            if (vatInput) {
                if (companyValue) {
                    vatInput.setAttribute("required", "required");
                    vatInput.classList.add("o_interdependent_required");
                    this._updateLabelRequired(vatInput, true);
                } else {
                    vatInput.removeAttribute("required");
                    vatInput.classList.remove("o_interdependent_required");
                    this._updateLabelRequired(vatInput, false);
                }
            }

            if (companyInput) {
                if (vatValue) {
                    companyInput.setAttribute("required", "required");
                    this._updateLabelRequired(companyInput, true);
                } else {
                    companyInput.removeAttribute("required");
                    this._updateLabelRequired(companyInput, false);
                }
            }
        } else {
            if (vatInput) {
                vatInput.removeAttribute("required");
                vatInput.classList.remove("o_interdependent_required");
                this._updateLabelRequired(vatInput, false);
            }
            if (companyInput) {
                companyInput.removeAttribute("required");
                this._updateLabelRequired(companyInput, false);
            }
        }
    },

    /**
     * Actualizeaza label-ul pentru a arata/ascunde asteriscul de required.
     */
    _updateLabelRequired: function (input, isRequired) {
        if (!input) return;
        const inputId = input.id;
        const label = this.el.querySelector(`label[for="${inputId}"]`);
        if (label) {
            if (isRequired) {
                label.classList.add("o_required_label");
            } else {
                label.classList.remove("o_required_label");
            }
        }
    },

    /**
     * Valideaza email-ul local (regex simplu).
     */
    _validateEmail: function (emailInput) {
        const value = (emailInput.value || "").trim();
        if (!value) {
            this._clearValidationFeedback(emailInput);
            return true;
        }

        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(value)) {
            this._showValidationError(emailInput, _t("Invalid email format."));
            return false;
        }

        this._showValidationSuccess(emailInput);
        return true;
    },

    /**
     * Valideaza telefonul local (lungime + format de baza).
     */
    _validatePhone: function (phoneInput, countryCode) {
        const raw = ((phoneInput && phoneInput.value) || "").trim();
        if (!raw) {
            if (phoneInput) {
                this._clearValidationFeedback(phoneInput);
            }
            return true;
        }

        const sanitized = raw.replace(/[^\d+]/g, "");
        const plusCount = (sanitized.match(/\+/g) || []).length;
        const normalized = plusCount > 1 ? sanitized.replace(/\+/g, "") : sanitized;

        const digits = normalized.replace(/\D/g, "");
        if (digits.length < 6) {
            this._showValidationError(phoneInput, _t("Phone number is too short."));
            return false;
        }

        if (countryCode === "RO" && !normalized.startsWith("+40") && !normalized.startsWith("0")) {
            this._showValidationWarning(
                phoneInput,
                _t("For Romania, start the number with +40 or 0 for a valid format.")
            );
            return true;
        }

        this._showValidationSuccess(phoneInput);
        return true;
    },

    /**
     * Valideaza CUI-ul romanesc.
     */
    _validateRomanianVat: function (vatInput) {
        let vat = vatInput.value.trim().toUpperCase();

        if (!vat) {
            this._clearValidationFeedback(vatInput);
            return false;
        }

        vat = vat.replace(/\s/g, "");

        const invalidChars = /[-._,;:!@#$%^&*()+={}\[\]|\\<>?\/~`'"]/;
        if (invalidChars.test(vat)) {
            this._showValidationError(
                vatInput,
                _t("The VAT number cannot contain special characters. Please enter digits only (e.g., 12345678).")
            );
            return false;
        }

        const vatNumber = vat.replace(/^RO/, "");

        if (!/^\d+$/.test(vatNumber)) {
            this._showValidationError(vatInput, _t("The VAT number must contain digits only. Example: 12345678"));
            return false;
        }

        if (vatNumber.length < 2) {
            this._showValidationError(vatInput, _t("The VAT number is too short. It must have at least 2 digits."));
            return false;
        }

        if (vatNumber.length > 10) {
            this._showValidationError(vatInput, _t("The VAT number is too long. A maximum of 10 digits are allowed."));
            return false;
        }

        this._showValidationSuccess(vatInput);
        return true;
    },

    /**
     * Valideaza numele companiei.
     */
    _validateCompanyName: function (companyInput) {
        const value = companyInput.value.trim();

        if (!value) {
            this._clearValidationFeedback(companyInput);
            return false;
        }

        const invalidPatterns = /^[-._\s]+$/;
        if (invalidPatterns.test(value)) {
            this._showValidationError(companyInput, _t("Please enter the full company name (e.g., SC EXAMPLE SRL)."));
            return false;
        }

        if (value.length < 3) {
            this._showValidationError(companyInput, _t("The company name must have at least 3 characters."));
            return false;
        }

        this._showValidationSuccess(companyInput);
        return true;
    },

    /**
     * Afiseaza indicator de incarcare.
     */
    _showLoadingIndicator: function (input) {
        input.classList.add("o_anaf_loading");

        let spinner = input.parentNode.querySelector(".o_anaf_spinner");
        if (!spinner) {
            spinner = document.createElement("span");
            spinner.className = "o_anaf_spinner position-absolute";
            spinner.innerHTML = '<i class="fa fa-spinner fa-spin text-muted"></i>';
            spinner.style.cssText = "right: 10px; top: 50%; transform: translateY(-50%);";

            const parent = input.parentNode;
            if (getComputedStyle(parent).position === "static") {
                parent.style.position = "relative";
            }

            parent.appendChild(spinner);
        }
    },

    /**
     * Ascunde indicatorul de incarcare.
     */
    _hideLoadingIndicator: function (input) {
        input.classList.remove("o_anaf_loading");

        const spinner = input.parentNode.querySelector(".o_anaf_spinner");
        if (spinner) {
            spinner.remove();
        }
    },

    /**
     * Afiseaza mesaj de eroare (Bootstrap 5).
     */
    _showValidationError: function (input, message) {
        this._clearValidationFeedback(input);

        input.classList.add("is-invalid");
        input.classList.remove("is-valid");

        const feedback = document.createElement("div");
        feedback.className = "invalid-feedback d-block o_vat_feedback";
        feedback.innerHTML = '<i class="fa fa-exclamation-circle me-1"></i>' + message;
        input.parentNode.insertBefore(feedback, input.nextSibling);
        // Dacă mesajul de eroare este un hint de duplicate, îl afișăm compact sub câmp
        if (message && message.toLowerCase().includes("already exists")) {
            this._showDuplicateHint(input, message);
        }
    },

    /**
     * Afiseaza mesaj de succes (Bootstrap 5).
     */
    _showValidationSuccess: function (input, message) {
        this._clearValidationFeedback(input);

        input.classList.add("is-valid");
        input.classList.remove("is-invalid");

        if (message) {
            const feedback = document.createElement("div");
            feedback.className = "valid-feedback d-block o_vat_feedback";
            feedback.innerHTML = '<i class="fa fa-check-circle me-1"></i>' + message;
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    },

    /**
     * Afiseaza mesaj de avertizare (pentru erori non-critice).
     */
    _showValidationWarning: function (input, message) {
        this._clearValidationFeedback(input);

        input.classList.add("is-valid");
        input.classList.remove("is-invalid");

        const feedback = document.createElement("div");
        feedback.className = "form-text text-warning d-block o_vat_feedback";
        feedback.innerHTML = '<i class="fa fa-exclamation-triangle me-1"></i>' + message;
        input.parentNode.insertBefore(feedback, input.nextSibling);
    },

    /**
     * Eliminam mesajele de validare existente.
     */
    _clearValidationFeedback: function (input) {
        input.classList.remove("is-invalid", "is-valid", "border-info");
        const feedbacks = input.parentNode.querySelectorAll(".o_vat_feedback, .invalid-feedback, .valid-feedback");
        feedbacks.forEach((fb) => fb.remove());

        // Ștergem hint-urile de duplicate de pe câmp
        this._removeHintsFor(input);
    },

    /**
     * Marchează în formular faptul că ANAF a răspuns cu succes (pentru server-side).
     */
    _markAnafStatus: function (isSuccess, vatInput, vatValue) {
        const form = vatInput && vatInput.form;
        if (!form) {
            return;
        }
        let flag = form.querySelector('input[name="anaf_ok"]');
        if (!flag) {
            flag = document.createElement("input");
            flag.type = "hidden";
            flag.name = "anaf_ok";
            form.appendChild(flag);
        }
        flag.value = isSuccess ? "1" : "";

        let vatField = form.querySelector('input[name="anaf_vat"]');
        if (!vatField) {
            vatField = document.createElement("input");
            vatField.type = "hidden";
            vatField.name = "anaf_vat";
            form.appendChild(vatField);
        }
        vatField.value = isSuccess && vatValue ? vatValue : "";
    },

    // ----------------------------------------------------------
    // Duplicate hints (UX)
    // ----------------------------------------------------------
    /**
     * Arată un hint compact sub câmpul invalid, cu CTA de login.
     */
    _showDuplicateHint: function (inputEl, message) {
        if (!inputEl) {
            return;
        }
        this._removeHintsFor(inputEl);
        const hint = document.createElement("div");
        hint.className = `form-text text-danger mt-1 ${DUPLICATE_HINT_CLASS}`;
        hint.innerHTML = `
            <i class="fa fa-exclamation-circle me-1"></i>
            ${message}
            <a class="btn btn-link btn-sm p-0 ms-1 o_duplicate_login_link" href="/web/login?redirect=/shop/checkout">
                ${_t("Sign in")}
            </a>
            <button type="button" class="btn btn-outline-primary btn-sm ms-2 o_duplicate_send_link">
                ${_t("Send access link")}
            </button>
            <span class="o_duplicate_status ms-2 text-muted"></span>
        `;
        inputEl.insertAdjacentElement("afterend", hint);
    },

    _removeHintsFor: function (inputEl) {
        if (!inputEl || !inputEl.parentNode) {
            return;
        }
        let sibling = inputEl.nextElementSibling;
        while (sibling && sibling.classList.contains(DUPLICATE_HINT_CLASS)) {
            const toRemove = sibling;
            sibling = sibling.nextElementSibling;
            toRemove.remove();
        }
    },

    _clearDuplicateHints: function () {
        this.el.querySelectorAll(`.${DUPLICATE_HINT_CLASS}`).forEach((node) => node.remove());
    },

    /**
     * Trimite link de acces (invitație/reset) prin RPC.
     */
    _onSendAccessLink: async function (ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        const container = btn.closest(`.${DUPLICATE_GLOBAL_MARKER}`) || 
                          btn.closest(`.${DUPLICATE_HINT_CLASS}`);
        const statusContainer = container ? container.querySelector(".o_duplicate_status_container") : null;
        const statusEl = statusContainer ? statusContainer.querySelector(".o_duplicate_status") : 
                         (container ? container.querySelector(".o_duplicate_status") : null);
        
        const emailInput = this._getEmailInput();
        const email = emailInput ? emailInput.value.trim() : "";
        
        if (!email) {
            if (statusEl) {
                statusEl.className = "o_duplicate_status";
                statusEl.innerHTML = `
                    <div class="alert alert-warning py-2 px-3 mb-0 d-inline-flex align-items-center">
                        <i class="fa fa-exclamation-triangle me-2"></i>
                        <span>${_t("Please enter your email address in the form above.")}</span>
                    </div>
                `;
            }
            if (emailInput) {
                emailInput.focus();
                emailInput.classList.add("is-invalid");
            }
            return;
        }
        this._sendAccessLink(email, statusEl);
    },

    async _sendAccessLink(email, statusEl) {
        const statusContainer = statusEl ? statusEl.closest(".o_duplicate_status_container") || statusEl.parentNode : null;
        
        if (statusEl) {
            statusEl.className = "o_duplicate_status";
            statusEl.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i>${_t("Sending email...")}`;
        }
        
        // Dezactivăm butonul în timpul trimiterii
        const sendBtn = statusContainer ? statusContainer.parentNode.querySelector(".o_duplicate_global_send_link") : null;
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.classList.add("disabled");
        }
        
        try {
            const res = await rpc("/shop/send_portal_access", {email});
            if (statusEl) {
                if (res.success) {
                    statusEl.className = "o_duplicate_status";
                    statusEl.innerHTML = `
                        <div class="alert alert-success py-2 px-3 mb-0 d-inline-flex align-items-center">
                            <i class="fa fa-check-circle me-2"></i>
                            <span>${res.message || _t("Email sent successfully! Check your inbox.")}</span>
                        </div>
                    `;
                } else {
                    statusEl.className = "o_duplicate_status";
                    statusEl.innerHTML = `
                        <div class="alert alert-danger py-2 px-3 mb-0 d-inline-flex align-items-center">
                            <i class="fa fa-exclamation-circle me-2"></i>
                            <span>${res.message || _t("Could not send the email.")}</span>
                        </div>
                    `;
                }
            }
        } catch (_e) {
            if (statusEl) {
                statusEl.className = "o_duplicate_status";
                statusEl.innerHTML = `
                    <div class="alert alert-danger py-2 px-3 mb-0 d-inline-flex align-items-center">
                        <i class="fa fa-exclamation-circle me-2"></i>
                        <span>${_t("Could not send the link. Please try again.")}</span>
                    </div>
                `;
            }
        } finally {
            // Reactivăm butonul
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.classList.remove("disabled");
            }
        }
    },

    /**
     * Injectează CTA global în alerta standard de erori (sus).
     */
    _injectGlobalDuplicateCTA: function () {
        // Rulează doar pe paginile cu formular (email prezent)
        const emailInput = this._getEmailInput();
        if (!emailInput) {
            return;
        }

        // Căutăm div-ul #errors din Odoo 18 (conține h5.text-danger)
        const errorsDiv = this.el.querySelector("#errors");
        if (errorsDiv && errorsDiv.children.length > 0) {
            this._transformErrorsDiv(errorsDiv);
        }

        // Căutăm și alertele clasice
        const alerts = this.el.querySelectorAll(".alert.alert-danger, .alert.alert-warning, .o_website_sale .alert.alert-danger");
        alerts.forEach((alertBox) => {
            // Verificăm dacă conține mesaje de duplicate
            const alertText = alertBox.textContent || "";
            const isDuplicateAlert = alertText.includes("Another partner already exists") || 
                                     alertText.includes("already exists with the");
            
            if (!isDuplicateAlert) {
                return;
            }

            // Simplificăm mesajele dacă există duplicate
            this._simplifyDuplicateAlert(alertBox);

            // Injectăm CTA
            if (alertBox.querySelector(`.${DUPLICATE_GLOBAL_MARKER}`)) {
                return;
            }

            this._appendCTAButtons(alertBox);
        });
    },

    /**
     * Transformă div-ul #errors din Odoo 18 într-o alertă profesională.
     */
    _transformErrorsDiv: function(errorsDiv) {
        const errorMessages = Array.from(errorsDiv.querySelectorAll("h5.text-danger, .text-danger"));
        const errorTexts = errorMessages.map(el => el.textContent || "").filter(t => t);
        
        // Verificăm dacă există mesaje de duplicate
        const fullText = errorTexts.join(" ");
        const isDuplicateError = fullText.includes("Another partner already exists") || 
                                  fullText.includes("already exists with the");
        
        if (!isDuplicateError) {
            return;
        }

        // Ascundem butonul standard "Already have an account? Sign in" pentru a evita duplicarea
        this._hideStandardSignInPrompt();

        // Extragem ce câmpuri sunt duplicate
        const duplicateFields = [];
        if (fullText.includes("VAT number") || fullText.includes("CUI")) {
            duplicateFields.push(_t("VAT/CUI"));
        }
        if (fullText.includes("email")) {
            duplicateFields.push(_t("Email"));
        }
        if (fullText.includes("phone number")) {
            duplicateFields.push(_t("Phone"));
        }

        // Transformăm div-ul într-o alertă profesională
        errorsDiv.className = "alert alert-warning o_duplicate_alert mb-3";
        errorsDiv.innerHTML = "";

        // Container principal cu icon
        const container = document.createElement("div");
        container.className = "d-flex align-items-start gap-3";

        // Icon mare
        const iconDiv = document.createElement("div");
        iconDiv.className = "o_duplicate_icon flex-shrink-0";
        iconDiv.innerHTML = '<i class="fa fa-user-circle fa-2x text-warning"></i>';
        container.appendChild(iconDiv);

        // Conținut
        const contentDiv = document.createElement("div");
        contentDiv.className = "flex-grow-1";

        // Titlu
        const title = document.createElement("h6");
        title.className = "alert-heading mb-1 fw-bold";
        title.innerHTML = '<i class="fa fa-exclamation-triangle me-1"></i>' + _t("Existing data found");
        contentDiv.appendChild(title);

        // Mesaj explicativ
        const message = document.createElement("p");
        message.className = "mb-2 small";
        if (duplicateFields.length > 0) {
            message.textContent = _t("We found existing data matching yours: ") + duplicateFields.join(", ") + ". ";
        } else {
            message.textContent = _t("We found existing data matching yours. ");
        }
        contentDiv.appendChild(message);

        // Instrucțiuni
        const instructions = document.createElement("p");
        instructions.className = "mb-3 small text-muted";
        instructions.textContent = _t("If you have an account, please sign in. Otherwise, click 'Get access link' to receive a login link by email.");
        contentDiv.appendChild(instructions);

        container.appendChild(contentDiv);
        errorsDiv.appendChild(container);

        // Adăugăm butoanele CTA
        this._appendCTAButtons(errorsDiv);
    },

    /**
     * Ascunde prompt-ul standard "Already have an account? Sign in" din Odoo.
     */
    _hideStandardSignInPrompt: function() {
        // Selectorul exact pentru div-ul din Odoo: div.float-end în #div_email_public
        const emailPublicDiv = this.el.querySelector("#div_email_public");
        if (emailPublicDiv) {
            const signInDiv = emailPublicDiv.querySelector('.float-end');
            if (signInDiv && signInDiv.textContent.includes("Already have an account")) {
                signInDiv.style.display = "none";
                signInDiv.classList.add("o_hidden_by_duplicate_alert");
            }
        }
        
        // Fallback: căutăm orice element care conține exact acest text
        const allDivs = this.el.querySelectorAll('div.float-end, div.align-items-center');
        allDivs.forEach(el => {
            const text = (el.textContent || "").trim();
            if (text.includes("Already have an account") && text.includes("Sign in")) {
                el.style.display = "none";
                el.classList.add("o_hidden_by_duplicate_alert");
            }
        });
    },

    /**
     * Adaugă butoanele CTA într-un container de alertă.
     */
    _appendCTAButtons: function(alertBox) {
        if (alertBox.querySelector(`.${DUPLICATE_GLOBAL_MARKER}`)) {
            return;
        }

        const emailInput = this._getEmailInput();
        const currentEmail = emailInput ? emailInput.value.trim() : "";
        const emailDisplay = currentEmail ? `<code class="mx-1">${currentEmail}</code>` : "";

        const container = document.createElement("div");
        container.className = `${DUPLICATE_GLOBAL_MARKER} o_duplicate_cta_container mt-3 pt-3 border-top`;
        
        container.innerHTML = `
            <div class="d-flex flex-column flex-sm-row gap-2 align-items-stretch align-items-sm-center">
                <a href="/web/login?redirect=/shop/checkout" class="btn btn-outline-primary">
                    <i class="fa fa-sign-in me-1"></i>${_t("I have an account - Sign in")}
                </a>
                <span class="text-muted d-none d-sm-inline">${_t("or")}</span>
                <button type="button" class="btn btn-primary o_duplicate_global_send_link">
                    <i class="fa fa-envelope me-1"></i>${_t("Get access link by email")}
                </button>
            </div>
            <div class="o_duplicate_status_container mt-2">
                <small class="o_duplicate_status text-muted">
                    ${currentEmail ? '<i class="fa fa-info-circle me-1"></i>' + _t("An access link will be sent to") + emailDisplay : ""}
                </small>
            </div>
        `;
        alertBox.appendChild(container);
    },

    /**
     * Simplifică mesajele duplicate într-un singur rezumat, mai curat.
     */
    _simplifyDuplicateAlert: function (alertBox) {
        if (!alertBox) {
            return false;
        }

        // Găsim noduri sau texte care conțin mesajele de dublură
        const alertText = alertBox.textContent || "";
        const containsDuplicateText = alertText.includes("Another partner already exists") || 
                                       alertText.includes("already exists with the");
        
        // Dacă nu există duplicate detectate în textul alertei, nu intervenim
        if (!containsDuplicateText) {
            return false;
        }

        // Ascundem butonul standard "Already have an account? Sign in"
        this._hideStandardSignInPrompt();

        // Extragem ce câmpuri sunt duplicate
        const duplicateFields = [];
        if (alertText.includes("VAT number") || alertText.includes("CUI")) {
            duplicateFields.push(_t("VAT/CUI"));
        }
        if (alertText.includes("email")) {
            duplicateFields.push(_t("Email"));
        }
        if (alertText.includes("phone number")) {
            duplicateFields.push(_t("Phone"));
        }

        // Curățăm conținutul alertei pentru a evita zgomotul vizual
        alertBox.innerHTML = "";
        alertBox.className = "alert alert-warning o_duplicate_alert mb-3";

        // Container principal cu icon
        const container = document.createElement("div");
        container.className = "d-flex align-items-start gap-3";

        // Icon mare
        const iconDiv = document.createElement("div");
        iconDiv.className = "o_duplicate_icon flex-shrink-0";
        iconDiv.innerHTML = '<i class="fa fa-user-circle fa-2x text-warning"></i>';
        container.appendChild(iconDiv);

        // Conținut
        const contentDiv = document.createElement("div");
        contentDiv.className = "flex-grow-1";

        // Titlu
        const title = document.createElement("h6");
        title.className = "alert-heading mb-1 fw-bold";
        title.innerHTML = '<i class="fa fa-exclamation-triangle me-1"></i>' + _t("Existing data found");
        contentDiv.appendChild(title);

        // Mesaj explicativ
        const message = document.createElement("p");
        message.className = "mb-2 small";
        if (duplicateFields.length > 0) {
            message.textContent = _t("We found existing data matching yours: ") + duplicateFields.join(", ") + ". ";
        } else {
            message.textContent = _t("We found existing data matching yours. ");
        }
        contentDiv.appendChild(message);

        // Instrucțiuni
        const instructions = document.createElement("p");
        instructions.className = "mb-3 small text-muted";
        instructions.textContent = _t("If you have an account, please sign in. Otherwise, click 'Get access link' to receive a login link by email.");
        contentDiv.appendChild(instructions);

        container.appendChild(contentDiv);
        alertBox.appendChild(container);

        return true;
    },

    /**
     * Observă adăugarea de alerte noi și injectează CTA/rezumat.
     */
    _observeAlerts: function () {
        // Observăm atât body-ul cât și div-ul #errors specific
        const errorsDiv = this.el.querySelector("#errors");
        
        const callback = () => {
            // Folosim un mic delay pentru a ne asigura că DOM-ul este actualizat
            setTimeout(() => this._injectGlobalDuplicateCTA(), 50);
        };
        
        const observer = new MutationObserver(callback);
        observer.observe(document.body, {childList: true, subtree: true});
        
        // Observăm specific div-ul #errors dacă există
        if (errorsDiv) {
            const errorsObserver = new MutationObserver(callback);
            errorsObserver.observe(errorsDiv, {childList: true, subtree: true, characterData: true});
            this._errorsObserver = errorsObserver;
        }
        
        this._alertsObserver = observer;
    },
});

export default publicWidget.registry.WebsiteVatValidation;
