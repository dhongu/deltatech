var dataChart = {
    labels: [],
    series: []
};

var optionsChart = {
    labelInterpolationFnc: function(value) {
        return value[0]
      },
    plugins: [ Chartist.plugins.tooltip() ]
};

var optionsTimeChart = {
    lineSmooth: Chartist.Interpolation.cardinal({
        fillHoles: true,
    }),
    axisX: {
        type: Chartist.FixedScaleAxis,
        divisor: 5,
        labelInterpolationFnc: function(value) {
          return moment(value).format('MMM D');
        }
    },
    plugins: [ Chartist.plugins.tooltip() ]
};

var responsiveOptions = [
    ['screen and (max-width: 640px)', {
        seriesBarDistance: 5,
        axisX: {
            labelInterpolationFnc: function(value) {
                return value[0];
            }
        }
    }]
];


var responsivePieOptions = [
  ['screen and (min-width: 640px)', {
    chartPadding: 30,
    labelOffset: 100,
    labelDirection: 'explode',
    labelInterpolationFnc: function(value) {
      return value;
    }
  }],
  ['screen and (min-width: 1024px)', {
    labelOffset: 80,
    chartPadding: 20
  }]
];


function ConvertDataChart(dataChart){
    for ( s in dataChart.series ) {
        for (d in dataChart.series[s].data) {
            dataChart.series[s].data[d].x = new Date( dataChart.series[s].data[d].x );
        }
    }
    return dataChart
}





