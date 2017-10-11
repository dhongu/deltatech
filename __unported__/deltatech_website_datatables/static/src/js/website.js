(function () {
'use strict';
var website = openerp.website;
var _t = openerp._t;


website.ready().then(function () {

	website.if_dom_contains('table.o_datatable', function () {

		var  language =  {
	        	"sEmptyTable":     _t("No data available in table"),
	        	"sInfo":           _t("Showing _START_ to _END_ of _TOTAL_ entries"),
	        	"sInfoEmpty":      _t("Showing 0 to 0 of 0 entries"),
	        	"sInfoFiltered":   _t("(filtered from _MAX_ total entries)"),
	        	"sInfoPostFix":    "",
	        	"sInfoThousands":  ",",
	        	"sLengthMenu":     _t("Show _MENU_ entries"),
	        	"sLoadingRecords": _t("Loading..."),
	        	"sProcessing":     _t("Processing..."),
	        	"sSearch":         _t("Search:"),
	        	"sZeroRecords":    _t("No matching records found"),
	        	"oPaginate": {
	        		"sFirst":    _t("First"),
	        		"sLast":     _t("Last"),
	        		"sNext":     _t("Next"),
	        		"sPrevious": _t("Previous")
	        	},
	        	"oAria": {
	        		"sSortAscending":  _t(": activate to sort column ascending"),
	        		"sSortDescending": _t(": activate to sort column descending")
	        	}
	        }

		$('.o_datatable').DataTable({
	        "language": language
	        }); 
	});
});






}());
