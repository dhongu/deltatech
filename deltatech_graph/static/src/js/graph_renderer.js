odoo.define('deltatech_graph.GraphRenderer', function (require) {

var GraphRenderer = require('web.GraphRenderer');
var config = require('web.config');
var field_utils = require('web.field_utils');


// hide top legend when too many items for device size
var MAX_LEGEND_LENGTH = 25 * (1 + config.device.size_class);


GraphRenderer.include({

    init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.discrete = params.discrete;
        this.colors = [
         '#377eb8','#e41a1c', '#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#999999',
        '#3182bd','#6baed6','#9ecae1','#c6dbef','#e6550d','#fd8d3c','#fdae6b','#fdd0a2','#31a354',
        '#74c476','#a1d99b','#c7e9c0','#756bb1','#9e9ac8','#bcbddc','#dadaeb','#636363','#969696','#bdbdbd','#d9d9d9'];
    },


   _renderDiscreteBarChart: function () {
        // prepare data for bar chart
        var self = this;
        var data, values;
        var measure = this.state.fields[this.state.measure].string;

        // zero groupbys
        if (this.state.groupedBy.length === 0) {
            data = [{
                values: [{
                    x: measure,
                    y: this.state.data[0].value}],
                key: measure
            }];
        }
        // one groupby
        if (this.state.groupedBy.length === 1) {
            values = this.state.data.map(function (datapt) {
                return {x: datapt.labels, y: datapt.value};
            });
            data = [
                {
                    values: values,
                    key: measure,
                }
            ];
        }
        if (this.state.groupedBy.length > 1) {
            var xlabels = [],
                series = [],
                label, serie, value;
            values = {};
            for (var i = 0; i < this.state.data.length; i++) {
                label = this.state.data[i].labels[0];
                serie = this.state.data[i].labels[1];
                value = this.state.data[i].value;
                if ((!xlabels.length) || (xlabels[xlabels.length-1] !== label)) {
                    xlabels.push(label);
                }
                series.push(this.state.data[i].labels[1]);
                if (!(serie in values)) {values[serie] = {};}
                values[serie][label] = this.state.data[i].value;
            }
            series = _.uniq(series);
            data = [];
            var current_serie, j;
            for (i = 0; i < series.length; i++) {
                current_serie = {values: [], key: series[i]};
                for (j = 0; j < xlabels.length; j++) {
                    current_serie.values.push({
                        x: xlabels[j],
                        y: values[series[i]][xlabels[j]] || 0,
                    });
                }
                data.push(current_serie);
            }
        }
        var svg = d3.select(this.$el[0]).append('svg');
        svg.datum(data);

        svg.transition().duration(0);

        var chart = nv.models.discreteBarChart();

        chart.options({
          margin: {left: 80, bottom: 100, top: 80, right: 0},
          delay: 100,
          transition: 10,
          showLegend: false,//_.size(data) <= MAX_LEGEND_LENGTH,
          showXAxis: true,
          color: function(d,i){
            return (d.data && d.data.color) || this.colors[i % this.colors.length]
          },
          showYAxis: true,
          rightAlignYAxis: false,
          stacked: this.stacked,
          showValues: true,
          reduceXTicks: false,
          rotateLabels: -20,
          showControls: (this.state.groupedBy.length > 1)
        });
        chart.yAxis.tickFormat(function (d) {
            var measure_field = self.state.fields[self.measure];
            return field_utils.format.float(d, {
                digits: measure_field && measure_field.digits || [69, 2],
            });
        });

        chart(svg);
        return chart;
    },


   _renderMultiBarChart: function () {
        // prepare data for bar chart
        var self = this;
        var data, values, domains;
        var measure = this.state.fields[this.state.measure].string;

        // zero groupbys
        if (this.state.groupedBy.length === 0) {
            data = [{
                values: [{
                    x: measure,
                    y: this.state.data[0].value,
                    domain:this.state.data[0].domain
                }],
                key: measure,
                color:false,

            }];
        }
        // one groupby
        if (this.state.groupedBy.length === 1) {
            values = this.state.data.map(function (datapt) {
                return {x: datapt.labels, y: datapt.value, domain:datapt.domain};
            });
            data = [
                {
                    values: values,
                    key: measure,
                    color: false
                }
            ];
        }
        if (this.state.groupedBy.length > 1) {
            var xlabels = [],
                series = [],
                series_color = [],
                label, serie, value ,color, domain;
            values = {};
            domains = {};
            for (var i = 0; i < this.state.data.length; i++) {
                label = this.state.data[i].labels[0];
                serie = this.state.data[i].labels[1];
                //color = this.state.data[i].labels[2];
                value = this.state.data[i].value;
                color = false;
                if ('color' in this.state.data[i]){
                    color = this.state.data[i].color;
                }


                if ((!xlabels.length) || (xlabels[xlabels.length-1] !== label)) {
                    xlabels.push(label);

                }
                series.push(this.state.data[i].labels[1]);

                if (!(serie in values)) {values[serie] = {};domains[serie]={}}
                values[serie][label] = this.state.data[i].value;
                domains[serie][label] = this.state.data[i].domain;
                series_color[serie] = color;

            }
            series = _.uniq(series);
            data = [];
            var current_serie, j;
            for (i = 0; i < series.length; i++) {
                current_serie = {values: [], key: series[i], color: series_color[series[i]]};
                for (j = 0; j < xlabels.length; j++) {
                    current_serie.values.push({
                        x: xlabels[j],
                        y: values[series[i]][xlabels[j]] || 0,
                        domain: domains[series[i]][xlabels[j]],
                    });
                }
                data.push(current_serie);
            }
        }
        var svg = d3.select(this.$el[0]).append('svg');
        svg.datum(data);

        svg.transition().duration(0);

        var chart = nv.models.multiBarChart();


        chart.options({
          margin: {left: 80, bottom: 100, top: 80, right: 0},
          delay: 100,
          transition: 10,

          color: function(d,i){
            return (d.values && d.values.color) || this.colors[i % this.colors.length]
          },

          showLegend: _.size(data) <= MAX_LEGEND_LENGTH,
          showXAxis: true,
          showYAxis: true,
          rightAlignYAxis: false,
          stacked: this.stacked,
          reduceXTicks: false,
          rotateLabels: -20,
          showControls: (this.state.groupedBy.length > 1)
        });

        chart.multibar.dispatch.on("elementClick", function(e) {
           e.state =  self.state;
           self.trigger_up('bar_click', e);
        });

        chart.yAxis.tickFormat(function (d) {
            var measure_field = self.state.fields[self.measure];
            return field_utils.format.float(d, {
                digits: measure_field && measure_field.digits || [69, 2],
            });
        });

        chart(svg);
        return chart;
    },



   _renderBarChart: function () {
        var self = this;
        var chart;

        if (this.discrete) {
            chart = this._renderDiscreteBarChart()
        }
        else {
            chart = this._renderMultiBarChart()
        }



        return chart;
    }

});



});