openerp.deltatech_import = function (instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    
    var base_import = instance.base_import;


    instance.web.DataImport.include({
        opts: [
            {name: 'encoding', label: _lt("Encoding:"), value: 'utf-8'},
            {name: 'separator', label: _lt("Separator:"), value: ','},
            {name: 'quoting', label: _lt("Quoting:"), value: '"'},
            {name: 'fromline', label: _lt("FromLine:"), value: '0'},
            {name: 'toline', label: _lt("ToLine:"), value: 'max'}
        ],

        onimport: function () {
            var self = this;
            return this.call_import({ dryrun: false }).done(function (message) {
                if (!_.any(message, function (message) {
                        return message.type === 'error' })) {
                    self['import_succeeded']([{
                        type: 'info',
                        message: _t("Import OK.")
                    }]);
                    return;
                }
                self['import_failed'](message);
            });
        },


    });
    
};
