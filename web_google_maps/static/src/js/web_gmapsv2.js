var map ;

openerp.gps_base = function(instance) {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    
    instance.gps_base.gps_base_gmap_marker = instance.web.form.FormWidget.extend({
        template: "gps_base_gmap_marker",
        init: function (view, code) {
            this._super(view, code);

            this.field_lat = code.attrs.lat;
            this.field_lng = code.attrs.lng;       

            //RPF: new field to use a reference to a gps coords record
            this.field_coords = code.attrs.coords;
            
            this.coord_lat=0;
            this.coord_lng=0;
        },
          
        start: function() {
            if (typeof google== 'undefined') {
                window.ginit = this.on_ready;
                $.getScript('http://maps.googleapis.com/maps/api/js?sensor=false&callback=ginit');           
            }
            else {
                this.on_ready();
            } 
           var self = this;
           self.on("change:effective_readonly", self, function() {
               //self.marker.setDraggable(self.get("effective_readonly") ? false : true);
           });
        },


        render_map: function (self, lat, lng){ 
            var myLatlng = new google.maps.LatLng(lat, lng); 
            var mapOptions = { 
                zoom: 8, 
                center: myLatlng 
            };

            var div_gmap = self.$el[0];

            map = new google.maps.Map(div_gmap, mapOptions);

            self.marker = new google.maps.Marker({ 
                position: myLatlng, 
                map: map, 
                draggable:false, 
            });

            google.maps.event.addListener(self.marker, 'dragend',function(NewPoint){ 
                lat = NewPoint.latLng.lat(); 
                lng = NewPoint.latLng.lng(); 
                self.update_latlng(lat,lng); 
            }); 
        },

    
        on_ready: function(){

            //RPF - begin
            var self=this;
            var lat = null;
            var lng = null;  
            var coords=null;


            if (self.field_lat && self.field_lng){
                var lat = self.field_manager.get_field_value(self.field_lat);
                var lng = self.field_manager.get_field_value(self.field_lng);
            }  
            else{
                if (self.field_coords){
                    try{
                        coords = self.field_manager.get_field_value(self.field_coords);
                    }
                    catch(err) {
                        alert("Error!\n\nMake sure the field '" + self.field_coords + "' is declared in the form.");
                    }
                }
                else{
                    alert("Error!\n\nCheck the widget attributes:\n\nOption 1: lat (float), lng (float);\nOption 2: coords (many2one - gps_base.coords)");
                }
            }


            function dump(obj) {
                var out = '';
                for (var i in obj) {
                    out += i + ": " + obj[i] + "\n";
                }
                alert(out);
            }
  
  
            function get_coordinates(coords_id, render_map){ 
                var call_back= render_map 
                var def = new $.Deferred(); 
                new instance.web.Model("gps_base.coords") 
                    .query(['latitude_aux','longitude_aux']) 
                    .filter([["id", "=", coords_id]]) 
                    .first() 
                    .then(function(result) { 
                        if(!result || result.length === 0){ 
                            call_back(self, 0, 0); 
                            def.reject(); 
                        }else{ 
                            call_back(self, result['latitude_aux'], result['longitude_aux']); 
                            def.resolve(); 
                        } 
                    });

                return def.promise(); 
            }
  
             
            //let's read the coordinates and populate the lat/lng vars 
            if (coords){ 
                return get_coordinates(coords, this.render_map); 
            }
            
            //VER ISTO
            //ver account_widgets.js (procurar por ".query(")
            //http://odoo-80.readthedocs.org/en/latest/reference/async.html
            
            //RPF - end


            var myLatlng = new google.maps.LatLng(lat, lng);
            var mapOptions = {
                zoom: 8,
                center: myLatlng
            };
            
            var div_gmap = self.$el[0];
            
            map = new google.maps.Map(div_gmap, mapOptions);

            self.marker = new google.maps.Marker({
                position: myLatlng,
                map: map,
                draggable:false,
            });    
            
            google.maps.event.addListener(this.marker, 'dragend',function(NewPoint){
                  lat = NewPoint.latLng.lat();
                  lng = NewPoint.latLng.lng();
                  self.update_latlng(lat,lng);
               });
               
            
            self.field_manager.on("field_changed:"+self.field_lat, self, self.display_result);
            self.field_manager.on("field_changed:"+self.field_lng, self, self.display_result);          
            
            //RPF
            self.field_manager.on("field_changed:"+self.field_coords, self, self.display_result);
        },

        update_latlng: function(lat, lng, coords ){
            var values = {};
            values[this.field_lat] = lat;
            values[this.field_lng] = lng; 
            
            //RPF
            values[this.field_coords] = coords; 
            
            this.field_manager.set_values(values).done(function() { });             
        },

        display_result: function() {
            var lat=0;
            try{
                lat = this.field_manager.get_field_value(this.field_lat);
            }  
            catch(err) {}
            
            var lng=0;
            try{
                lng = this.field_manager.get_field_value(this.field_lng);
            }  
            catch(err) {}

            //RPF
            var coords=null;
            try{
                coords = this.field_manager.get_field_value(this.field_coords);
            }  
            catch(err) {}

            var myLatlng = new google.maps.LatLng(lat, lng);
            map.setCenter(myLatlng);  
            this.marker.setPosition(myLatlng); 
        },
        

 
 });

instance.web.form.custom_widgets.add('gps_base_gmap_marker', 'instance.gps_base.gps_base_gmap_marker');
     
instance.web.views.add('gmaps', 'instance.gps_base.gmaps');

 
instance.gps_base.gmaps = instance.web.View.extend({

     template: 'Gmaps',

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
         this.$el.html(QWeb.render("Gmaps", {"fields_view": this.fields_view, 'elem_id': this.elem_id}));

         
         if (typeof google== 'undefined') {
             window.ginit = this.on_ready;
             $.getScript('http://maps.googleapis.com/maps/api/js?&sensor=false&callback=ginit');             
         }
         else {
             this.on_ready();
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
     },
     
     
 
     do_load_record: function(record){
         var self = this;
         _(self.fields_view.arch.children).each(function(data){
             self.do_add_item(data,record)
         });
     },

     do_add_item: function(item,record){
         var self = this;
         if (item.tag == 'widget' && item.attrs.type == 'gps_base_gmap_marker' ){

             var myLatlng = new google.maps.LatLng(record[item.attrs.lat], record[item.attrs.lng]);
             var marker = new google.maps.Marker({
                 position: myLatlng,
                 map: map,
                 draggable:false,
             });             
         }
     },
 });
 
};







// vim:et fdc=0 fdl=0:
