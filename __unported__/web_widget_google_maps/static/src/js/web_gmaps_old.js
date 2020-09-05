openerp.web_widget_google_maps = function (instance) {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var map ;
    
 instance.web_widget_google_maps.gmap_marker = instance.web.form.FormWidget.extend({
        template: "gmap_marker",




        init: function (view, code) {
            this._super(view, code);
            this.field_lat = code.attrs.lat;
            this.field_lng = code.attrs.lng;
            this.shown = $.Deferred();
        },
          
        start: function() {

            if (typeof google== 'undefined') {
                window.ginit = this.on_ready;
                $.getScript('http://maps.googleapis.com/maps/api/js?sensor=false&callback=ginit');        	 
            }
            else {
                setTimeout(function () { self.on_ready(); }, 1000);

                //window.ginit = this.on_ready;
                //$.getScript('http://maps.googleapis.com/maps/api/js?sensor=false&callback=ginit');
            }
           var self = this;
           self.on("change:effective_readonly", self, function() {
               self.marker.setDraggable(self.get("effective_readonly") ? false : true);
           });

           //this.shown.done(this.proxy('on_ready'));
           return this._super();

        },



        on_ready: function(){
            var lat = this.field_manager.get_field_value(this.field_lat);
            var lng = this.field_manager.get_field_value(this.field_lng);  

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
                draggable:false,
            });    
             
            var my_self= this;  
            
            google.maps.event.addListener(this.marker, 'dragend',function(NewPoint){
                  lat = NewPoint.latLng.lat();
                  lng = NewPoint.latLng.lng();
                  my_self.update_latlng(lat,lng);
               });
               
            
            this.field_manager.on("field_changed:"+this.field_lat, this, this.display_result);
            this.field_manager.on("field_changed:"+this.field_lng, this, this.display_result);



            //bounds.extend(myLatlng);
            //map.fitBounds(bounds);       # auto-zoom
            //map.panToBounds(bounds);     # auto-center

            google.maps.event.trigger( map, 'resize')
        },

        update_latlng: function(lat, lng ){
            var values = {};
            values[this.field_lat] = lat;
            values[this.field_lng] = lng; 
            this.field_manager.set_values(values).done(function() { });             
        },

        display_result: function() {
            var lat = this.field_manager.get_field_value(this.field_lat);
            var lng = this.field_manager.get_field_value(this.field_lng);  
            var myLatlng = new google.maps.LatLng(lat, lng);
            map.setCenter(myLatlng);  
            this.marker.setPosition(myLatlng);
            google.maps.event.trigger( map, 'resize')

        },
        

 
 });

 instance.web.form.custom_widgets.add('gmap_marker', 'instance.web_widget_google_maps.gmap_marker');

 
 instance.web_widget_google_maps.gmap_route = instance.web.form.FormWidget.extend({
        template: "gmap_route",

        init: function (view, code) {
            this._super(view, code);
            this.field_from_lat = code.attrs.from_lat;
            this.field_from_lng = code.attrs.from_lng;
            this.field_to_lat = code.attrs.to_lat;
            this.field_to_lng = code.attrs.to_lng; 
            
            this.field_distance = code.attrs.distance; 
            this.field_duration = code.attrs.duration;  
            
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
            var from_lat = this.field_manager.get_field_value(this.field_from_lat);
            var from_lng = this.field_manager.get_field_value(this.field_from_lng); 
            var to_lat = this.field_manager.get_field_value(this.field_to_lat);
            var to_lng = this.field_manager.get_field_value(this.field_to_lng);
                                  
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
            

            this.field_manager.on("field_changed:"+this.field_from_lat, this, this.display_result);
            this.field_manager.on("field_changed:"+this.field_from_lng, this, this.display_result);     
            this.field_manager.on("field_changed:"+this.field_to_lat, this, this.display_result);
            this.field_manager.on("field_changed:"+this.field_to_lng, this, this.display_result);            
    
           self.on("change:effective_readonly", self, function() {
               var rendererOptions = {
                  draggable: self.get("effective_readonly") ? false : true
               };              
               self.directionsDisplay.setOptions(rendererOptions);
           }); 
           
           google.maps.event.addListener(self.directionsDisplay, 'directions_changed', function() {
                if (!self.get("effective_readonly")){
                      self.computeTotal(self.directionsDisplay.getDirections());
                  }
                
              });
           
           this.display_result();

           this.updating = false;            	
        },

        display_result: function() {
            
            if (this.updating) return;
            var self = this;
            

            var from_lat = this.field_manager.get_field_value(this.field_from_lat);
            var from_lng = this.field_manager.get_field_value(this.field_from_lng); 
            var to_lat = this.field_manager.get_field_value(this.field_to_lat);
            var to_lng = this.field_manager.get_field_value(this.field_to_lng);  
            
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
                  if (!self.get("effective_readonly")){
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
          var values = {};
 
          values[this.field_distance] = distance;
          values[this.field_duration] = duration; 
 
          values[this.field_from_lat] = result.Lb.origin.lat();
          values[this.field_from_lng] = result.Lb.origin.lng(); 
          
          values[this.field_to_lat] = result.Lb.destination.lat();
          values[this.field_to_lng] = result.Lb.destination.lng();
          
          this.updating = true;
          this.field_manager.set_values(values).done(function() { 
              self.updating = false;
              });   
          
        },


 });
 instance.web.form.custom_widgets.add('gmap_route', 'instance.web_widget_google_maps.gmap_route');

 
 
	 
instance.web.views.add('gmaps', 'instance.web_widget_google_maps.gmaps');
 
 
instance.web_widget_google_maps.gmaps = instance.web.View.extend({

     template: 'gmaps',

     init: function(parent, dataset, view_id, options) {
         this._super(parent);
         this.set_default_options(options);
         this.view_manager = parent;
         this.dataset = dataset;
         this.dataset_index = 0;
         this.model = this.dataset.model;
         this.view_id = view_id;
         this.view_type = 'gmaps';


     },
     

 
     view_loading: function(data) {

         var self = this;
         this.fields_view = data;
         
         //_.each(data.geoengine_layers.actives, function(item) {
         //    self.geometry_columns[item.geo_field_id[1]] = true;
         //});
         this.$el.html(QWeb.render("gmaps", {"fields_view": this.fields_view, 'elem_id': this.elem_id}));

         
         if (typeof google== 'undefined') {
             window.ginit = this.on_ready;
             $.getScript('http://maps.googleapis.com/maps/api/js?&sensor=false&callback=ginit');        	 
         }
         else {
        	 setTimeout(function () { self.on_ready(); }, 1000);
         }
     },

     
     on_ready: function() {
 

    	 var myLatlng = new google.maps.LatLng(45, 25);
         var mapOptions = {
             zoom: 8,
             center: myLatlng
         };
         
         var div_gmap = this.$el[0];
         
         map = new google.maps.Map(div_gmap, mapOptions); 
         
         this.directionsService = new google.maps.DirectionsService();

         
         
         var self = this;
         self.dataset.read_slice(_.keys(self.fields_view.fields)).then(function(data){
             _(data).each(self.do_load_record); 
         });
          google.maps.event.trigger( map, 'resize')
     },
     
     
 
     do_load_record: function(record){
    	 var self = this;
    	 _(self.fields_view.arch.children).each(function(data){
    		 self.do_add_item(data,record)
    	 });
     },

     do_add_item: function(item,record){
    	 var self = this;
    	 if (item.tag == 'widget' && item.attrs.type == 'gmap_marker' ){

        	 var myLatlng = new google.maps.LatLng(record[item.attrs.lat], record[item.attrs.lng]);
             var marker = new google.maps.Marker({
                 position: myLatlng,
                 map: map,
                 draggable:false,
             });     		 
    	 }
    	 if (item.tag == 'widget' && item.attrs.type == 'gmap_route' ){

             var from_lat = record[item.attrs.from_lat] 
             var from_lng =  record[item.attrs.from_lng]
             var to_lat =  record[item.attrs.to_lat]
             var to_lng =   record[item.attrs.to_lng]
             

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
    	 
  	 
     },

 });
 
 
 
 
 


 
};



