
                var testdata = [
                {key: "One", y: 5},
                {key: "Two", y: 2},
                {key: "Three", y: 9},
                {key: "Four", y: 7},
                {key: "Five", y: 4},
                {key: "Six", y: 3},
                {key: "Seven", y: 0.5}
                ];

                var width = 300;
                var height = 300;

                nv.addGraph(function() {
                var chart = nv.models.pie()
                .x(function(d) { return d.key; })
                .y(function(d) { return d.y; })
                .width(width)
                .height(height)

                ;

                d3.select("#test1")
                .datum([testdata])
                .transition().duration(1200)
                .attr('width', width)
                .attr('height', height)
                .call(chart);

                return chart;
                });