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
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

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
    },

    /**
     * Initializare widget.
     */
    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._setupValidation();
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
                    if (code === "RO" || text.includes("romania") || text.includes("românia")) {
                        countrySelect.value = option.value;
                        countrySelect.dispatchEvent(new Event("change", { bubbles: true }));
                        countrySelect.scrollIntoView({ behavior: "smooth", block: "center" });

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
            } else if (result.error) {
                this._showValidationWarning(vatInput, result.error);
            }
        } catch (error) {
            console.error("ANAF lookup error:", error);
            this._showValidationWarning(
                vatInput,
                _t("Couldn't verify the VAT number. You can continue manually.")
            );
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
                    stateSelect.dispatchEvent(new Event("change", { bubbles: true }));
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
        const raw = (phoneInput?.value || "").trim();
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

        if (vatNumber.startsWith("0")) {
            this._showValidationError(
                vatInput,
                _t("Romanian VAT numbers cannot start with 0. Please check the value.")
            );
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
    },
});

export default publicWidget.registry.WebsiteVatValidation;
