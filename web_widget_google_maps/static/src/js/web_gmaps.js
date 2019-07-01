odoo.define('web_widget_google_maps', function (require) {
"use strict";

var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var Widget = require('web.Widget');
var FormView = require('web.FormView');

var view_registry = require('web.view_registry');
var registry = require('web.field_registry');
var widgetRegistry = require('web.widget_registry');

var BasicView = require('web.BasicView');
var BasicController = require('web.BasicController');
var BasicRenderer = require('web.BasicRenderer');

var AbstractView = require('web.AbstractView');
var AbstractModel = require('web.AbstractModel');
var AbstractController = require('web.AbstractController');
var AbstractRenderer = require('web.AbstractRenderer');



var map ;



var GMapMarker = Widget.extend({
        template: "gmap_marker",

        init: function (view, record, node) {
            this._super(view, record, node);
            this.field_lat =    node.attrs.lat;
            this.field_lng =   node.attrs.lng;
            this.shown = $.Deferred();
            this.data = record.data;
            this.mode = view.mode || "readonly";
            this.record = record;
            this.view = view;
            var self = this;

            self._rpc({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ['google_maps_api_key']
                }).then(function (key) {
                    self.google_maps_api_key = key;

                    $.getScript('https://maps.googleapis.com/maps/api/js?callback=ginit&key='+ self.google_maps_api_key);
            });




        },

        start: function() {
            var self = this;
            if (typeof google== 'undefined') {
                window.ginit = this.on_ready;
                // maps.google.com/maps/api/js?key=#{google_maps_api_key}
                //$.getScript('http://maps.googleapis.com/maps/api/js?sensor=false&callback=ginit');

            }
            else {
                setTimeout(function () { self.on_ready(); }, 1000);
            }
           return this._super();

        },



        on_ready: function(){
            var lat = this.data[this.field_lat];
            var lng = this.data[this.field_lng];

            var myLatlng = new google.maps.LatLng(lat, lng);
            var bounds  = new google.maps.LatLngBounds();

            var mapOptions = {
                zoom: 8,
                center: myLatlng
            };
            
            var div_gmap = this.$el[0];
            
            map = new google.maps.Map(div_gmap, mapOptions);

            this.marker = new google.maps.Marker({
                position: myLatlng,
                map: map,
                draggable: this.mode=='edit'? true : false,
            });    
             
            var my_self= this;  
            
            google.maps.event.addListener(this.marker, 'dragend',function(NewPoint){
                  lat = NewPoint.latLng.lat();
                  lng = NewPoint.latLng.lng();
                  my_self.update_latlng(lat,lng);
               });
               
            this.view.on("field_changed:"+this.field_lat, this, this.display_result);
            this.view.on("field_changed:"+this.field_lng, this, this.display_result);


            //bounds.extend(myLatlng);
            //map.fitBounds(bounds);       # auto-zoom
            //map.panToBounds(bounds);     # auto-center

            google.maps.event.trigger( map, 'resize')
        },

        update_latlng: function(lat, lng ){

            this.data[this.field_lat] = lat;
            this.data[this.field_lng] = lng;


            var def = $.Deferred();
            var changes = {};
            changes[this.field_lat] = lat;
            changes[this.field_lng] = lng;

            this.trigger_up('field_changed', {
                dataPointID: this.record.id,
                changes: changes,
                onSuccess: def.resolve.bind(def),
                onFailure: def.reject.bind(def),
            });

        },

        display_result: function() {
            var lat = this.data[this.field_lat];
            var lng = this.data[this.field_lng];
            var myLatlng = new google.maps.LatLng(lat, lng);
            map.setCenter(myLatlng);  
            this.marker.setPosition(myLatlng);
            google.maps.event.trigger( map, 'resize')

        },
        

 
 });

core.form_custom_registry.add('gmap_marker', GMapMarker);
widgetRegistry.add('gmap_marker', GMapMarker);
 
var GMapRoute =  Widget.extend({
        template: "gmap_route",

        init: function (view, record, node) {
            this._super(view, record);
            this.field_from_lat = node.attrs.from_lat;
            this.field_from_lng = node.attrs.from_lng;
            this.field_to_lat = node.attrs.to_lat;
            this.field_to_lng = node.attrs.to_lng;
            
            this.field_distance = node.attrs.distance;
            this.field_duration = node.attrs.duration;

            this.shown = $.Deferred();
            this.data = record.data;
            this.mode = view.mode || "readonly";
            this.record = record;
            this.view = view;
        },       
        
        start: function () {
            var self = this;
            if (typeof google== 'undefined') {
                window.ginit = this.on_ready;
                $.getScript('http://maps.googleapis.com/maps/api/js?&sensor=false&callback=ginit');        	 
            }
            else {
           	 setTimeout(function () { self.on_ready(); }, 1000);
            }

        },
        
        on_ready: function(){
            var self = this;

            var from_lat = this.data[this.field_from_lat];
            var from_lng = this.data[this.field_from_lng];
            var to_lat = this.data[this.field_to_lat];
            var to_lng = this.data[this.field_to_lng];
                                  
            var div_gmap = this.$el[0];
                        
            var from_Latlng = new google.maps.LatLng(from_lat, from_lng);
            var to_Latlng = new google.maps.LatLng(to_lat, to_lng);
            
            var mapOptions = {
                zoom: 8,
                center: from_Latlng
            };
            
            map = new google.maps.Map(div_gmap,mapOptions);
            
            this.directionsService = new google.maps.DirectionsService();
            
            this.directionsDisplay = new google.maps.DirectionsRenderer();
            this.directionsDisplay.setMap(map);
            

            //this.field_manager.on("field_changed:"+this.field_from_lat, this, this.display_result);
            //this.field_manager.on("field_changed:"+this.field_from_lng, this, this.display_result);
            //this.field_manager.on("field_changed:"+this.field_to_lat, this, this.display_result);
            //this.field_manager.on("field_changed:"+this.field_to_lng, this, this.display_result);
    

           var rendererOptions = {
               draggable: this.mode=='edit'? true : false,
           };
           self.directionsDisplay.setOptions(rendererOptions);

           
           google.maps.event.addListener(self.directionsDisplay, 'directions_changed', function() {
                if (self.mode=='edit'){
                      self.computeTotal(self.directionsDisplay.getDirections());
                  }
                
              });
           
           this.display_result();

           this.updating = false;            	
        },

        display_result: function() {
            
            if (this.updating) return;
            var self = this;
            

            var from_lat = this.data[this.field_from_lat];
            var from_lng = this.data[this.field_from_lng];
            var to_lat = this.data[this.field_to_lat];
            var to_lng = this.data[this.field_to_lng];
            
            if (from_lat==0 | from_lng==0 | to_lat==0 | to_lng==0)
                return;
            var from_Latlng = new google.maps.LatLng(from_lat, from_lng);
            var to_Latlng = new google.maps.LatLng(to_lat, to_lng);         
            var request = {
                  origin:from_Latlng,
                  destination:to_Latlng,
                  travelMode: google.maps.TravelMode.DRIVING
            };
            self.directionsService.route(request, function(response, status) {
                if (status == google.maps.DirectionsStatus.OK) {
                  self.directionsDisplay.setDirections(response);
                  if (self.mode=='edit'){
                      self.computeTotal(response);
                  }
                }
            });
             google.maps.event.trigger( map, 'resize')
        },
        
        
      computeTotal: function(result) {
            var self = this;
            var distance = 0;
            var duration = 0;
            var myroute = result.routes[0];
            for (var i = 0; i < myroute.legs.length; i++) {
            distance += myroute.legs[i].distance.value;
            duration += myroute.legs[i].duration.value;

            }
            distance = distance / 1000.0;
            duration = duration / 60 / 60;
            this.updating = true;

            var changes = {};

            if (result.request.origin.location != undefined) {
                changes[this.field_from_lat] = result.request.origin.location.lat();
                changes[this.field_from_lng] = result.request.origin.location.lng();
            }
            else {
                changes[this.field_from_lat] = result.request.origin.lat();
                changes[this.field_from_lng] = result.request.origin.lng();
            }

            if (result.request.destination.location != undefined) {
                changes[this.field_to_lat] = result.request.destination.location.lat();
                changes[this.field_to_lng] = result.request.destination.location.lng();
            }
            else {
                changes[this.field_to_lat] = result.request.destination.lat();
                changes[this.field_to_lng] = result.request.destination.lng();
            }

            var def = $.Deferred();

            if (this.field_distance != undefined) {
                changes[this.field_distance] = distance;
            }
            if (this.field_duration) {
                changes[this.field_duration] = duration;
            }
            this.trigger_up('field_changed', {
                dataPointID: this.record.id,
                changes: changes,
                onSuccess: def.resolve.bind(def),
                onFailure: def.reject.bind(def),
            });


        },


 });

core.form_custom_registry.add('gmap_route', GMapRoute);
widgetRegistry.add('gmap_route', GMapRoute);


/////////////////////////////////////////////////
// gather the fields to get
var fieldsToGather = [
    "lat",
    "lng",
];

var GMapsModel = AbstractModel.extend({

});

var GMapsController = BasicController.extend({
});


var GMapsRenderer = BasicRenderer.extend({
    template: 'gmaps',

    init: function (parent, state, params) {
        this._super.apply(this, arguments);
    },

    start: function () {
        var self = this;
        var myLatlng = new google.maps.LatLng(46, 25);
        var mapOptions = {
            zoom: 8,
            center: myLatlng
        };
        var div_gmap = this.$el[0];
        this.map = new google.maps.Map(div_gmap, mapOptions);

        this.directionsService = new google.maps.DirectionsService();
        return this._super();


    },

    _render: function () {
        var div_gmap = this.$el[0];

        $(div_gmap).css({'position':'absolute'});
        var self = this;
        _(this.state.data).each(self.do_load_record);
        google.maps.event.trigger( this.map, 'resize')
        return this._super.apply(this, arguments);

    },

    do_load_record: function(record){
    	 var self = this;
    	 _(self.arch.children).each(function(data){
    		 self.do_add_item(data,record.data)
    	 });
     },

    do_add_item: function(item,data){
    	 var self = this;
    	 if (item.tag == 'widget' && item.attrs.name == 'gmap_marker' ){
        	 var myLatlng = new google.maps.LatLng(data[item.attrs.lat], data[item.attrs.lng]);
             var title = data[item.attrs.description];
             var marker = new google.maps.Marker({
                 position: myLatlng,
                 map: this.map,
                 title:title,
                 draggable:false,
             });
    	 };

         if (item.tag == 'widget' && item.attrs.name == 'gmap_markers' ){
        	 var myLatlng = new google.maps.LatLng(data[item.attrs.lat], data[item.attrs.lng]);
             var title = data[item.attrs.description];
             var marker = new google.maps.Marker({
                 position: myLatlng,
                 map: this.map,
                 title:title,
                 draggable:false,
             });
    	 };

    	 if (item.tag == 'widget' && item.attrs.name == 'gmap_route' ){

             var from_lat = data[item.attrs.from_lat]
             var from_lng =  data[item.attrs.from_lng]
             var to_lat =  data[item.attrs.to_lat]
             var to_lng =   data[item.attrs.to_lng]

             var from_Latlng = new google.maps.LatLng(from_lat, from_lng);
             var to_Latlng = new google.maps.LatLng(to_lat, to_lng);
             var request = {
                   origin:from_Latlng,
                   destination:to_Latlng,
                   travelMode: google.maps.TravelMode.DRIVING
             };
             var directionsDisplay = new google.maps.DirectionsRenderer();
             directionsDisplay.setMap(map);
             self.directionsService.route(request, function(response, status) {
                 if (status == google.maps.DirectionsStatus.OK) {
                   directionsDisplay.setDirections(response);
                 }
             });
    	 }


    }

});




var GMaps = BasicView.extend({

     display_name: _lt('Map'),
     icon: 'fa-map-marker',
     accesskey: "g",

     config: _.extend({}, BasicView.prototype.config, {
       // Model: GMapsModel,
        Controller: GMapsController,
        Renderer: GMapsRenderer,
     }),
     viewType: 'gmaps',
     jsLibs: ['http://maps.googleapis.com/maps/api/js?&sensor=false'],


     init: function (viewInfo, params) {
        this._super.apply(this, arguments);
        var arch = viewInfo.arch;
        var fields = viewInfo.fields;
        var attrs = arch.attrs;
        var mode = arch.attrs.editable && !params.readonly ? "edit" : "readonly";
        this.controllerParams.mode = mode;
     },


     init_old: function(parent, dataset, view_id, options) {
         this._super(parent);
         this.set_default_options(options);
         this.view_manager = parent;
         this.dataset = dataset;
         this.dataset_index = 0;
         this.model = this.dataset.model;
         this.view_id = view_id;
         this.view_type = 'gmaps';
     },
     

 

 });
 
 
view_registry.add('gmaps', GMaps)
 
 
return {
    gmap_marker: GMapMarker,
    gmap_route: GMapRoute,
    gmaps:GMaps
};

 

});


