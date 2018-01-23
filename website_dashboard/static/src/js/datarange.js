    var locale =  {
        "format": "DD.MM.YYYY",
        "separator": " - ",
        "applyLabel": "Aplica",
        "cancelLabel": "Cancel",
        "fromLabel": "De la",
        "toLabel": "Pana la",
        "customRangeLabel": "Particular",
        "weekLabel": "S",
        "daysOfWeek": [ "Du","Lu", "Ma","Me", "Jo","Vi","Sa" ],
        "monthNames": [
            "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
            "Iulie",  "August", "Septembrie", "Octombrie", "Noiembrie",  "Decembrie"
        ],
        "firstDay": 1
    }

    //$('input[name="daterange"]').daterangepicker({"locale": locale});


    var vars = [], hash;
        var q = document.URL.split('?')[1];
        if(q != undefined){
            q = q.split('&');
            for(var i = 0; i < q.length; i++){
                hash = q[i].split('=');
                vars.push(hash[1]);
                vars[hash[0]] = hash[1];
            }
    }
    if (vars['start'] == undefined ){
        vars['start'] = '2018-01-01';
        vars['end'] = '2018-12-31';
    }

    var start = moment(vars['start'], "YYYY-MM-DD");
    var end = moment(vars['end'], "YYYY-MM-DD");

    $('#reportrange span').html(start.format('DD.MM.YYYY') + ' - ' + end.format('DD.MM.YYYY'));

    function cb(start, end) {
        window.location =  $(location).attr('origin')+$(location).attr('pathname')+
                            '?start='+start.format('YYYY-MM-DD')+'&end='+ end.format('YYYY-MM-DD');
    }

    $('#reportrange').daterangepicker({
        startDate: start,
        endDate: end,
        locale : locale,
        ranges: {
           'Azi': [moment(), moment()],
           'Ieri': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Last 7 Days': [moment().subtract(6, 'days'), moment()],
           'Last 30 Days': [moment().subtract(29, 'days'), moment()],
           'Luna aceasta': [moment().startOf('month'), moment().endOf('month')],
           'Luna trecuta': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
           'Anul aceasta': [moment().startOf('year'), moment().endOf('year')],
           'Anul trecut': [moment().subtract(1, 'year').startOf('year'), moment().subtract(1, 'year').endOf('year')]
        }
    }, cb);



