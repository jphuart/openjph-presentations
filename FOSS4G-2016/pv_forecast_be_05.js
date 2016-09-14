$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (null == results){
        if (name=='myday'){
            return 'today';
        } else{
            return null;
        }
    } else {
        if (name=='myday'){
            //customisation to always have a valid value for myday
            if (['today', 'tomorrow'].indexOf(results[1]) >= 0) {
                return results[1] || 0;
            } else {
                return 'today';
            }
        }
        return results[1] || 0;
    }
    
}

var PvForecastBe_05 = {
    // variables
    myday : $.urlParam('myday'),
    map_be : [],
    summaryData : [],    
    startHour : 6,
    endHour : 17,
    slideIndex : 1,    
//    slider : $("#slide"),
//    hrDisplay : $("#slidevalue"),
    timer : 0,
    /* always fit these bounds in the window */
    beBounds : [[ 51.49, 2.54],[49.49, 6.42]],
    /* solar image bounds in  EPSG31370 */
//    beimgBounds : L.bounds([11200.00, 244000.00],[308350.00, 21000.00]),
    beimgBounds : L.bounds([12500.00, 244000.00],[308600.00, 21000.00]),
    /* define the projection used by the map */
    belProjection : "+proj=lcc +lat_1=51.16666723333333 +lat_2=49.8333339 +lat_0=90 +lon_0=4.367486666666666 +x_0=150000.013 +y_0=5400088.438 +ellps=intl +towgs84=-106.869,52.2978,-103.724,0.3366,-0.457,1.8422,-1.2747 +units=m +no_defs",
    EPSG31370 : new L.Proj.CRS("urn:ogc:def:crs:EPSG::31370", 
            "+proj=lcc +lat_1=51.16666723333333 +lat_2=49.8333339 +lat_0=90 +lon_0=4.367486666666666 +x_0=150000.013 +y_0=5400088.438 +ellps=intl +towgs84=-106.869,52.2978,-103.724,0.3366,-0.457,1.8422,-1.2747 +units=m +no_defs",
                        {
                            resolutions: [8192, 4096, 2048, 1024, 512, 256, 128],
                            origin: [0, 0]
                          }),

    // init & events
    onReady : function () {
        var curindex, disdate;
        if (myday == 'today'){
            $("#today").addClass('selected');
            $("#tomorrow").removeClass('selected');
        } else {
            $("#today").removeClass('selected');
            $("#tomorrow").addClass('selected');
        }
        /* load summary data */
        PvForecastBe_05.startHour = PvForecastBe_05.summaryData.start_hour;
        PvForecastBe_05.endHour = PvForecastBe_05.summaryData.end_hour;
        disdate = PvForecastBe_05.summaryData.date.slice(-2)+'/'+PvForecastBe_05.summaryData.date.slice(5,7)+'/'+PvForecastBe_05.summaryData.date.slice(0,4);
        $("#ifr-date span:first-child").html(disdate);
        $("#slide").attr("min", PvForecastBe_05.startHour);
        $("#slide").attr("max", PvForecastBe_05.endHour - 1);
        /**
        date
        utc_offset
        zpoints
            pt#
                clearsky_textual
                graph_plage
                latitude
                longitude
                peak
                plage
                solptname
        */
        /* build the map */
        PvForecastBe_05.buildMap();
        
        /* add the solar image as background layer */
        PvForecastBe_05.sl = [];
        for (i = 0; i < (PvForecastBe_05.endHour - PvForecastBe_05.startHour); i++) {
            curindex = PvForecastBe_05.startHour + i;
            PvForecastBe_05.sl[i] ={id: 'sl_' + curindex, layer : PvForecastBe_05.addSolarLayer('./data/map_hourly_' + PvForecastBe_05.myday + '_' + curindex + '.png', 'sl_' + curindex)};
        }
        /* add the daily synthesis map */
        PvForecastBe_05.sl[i] = {id: 'sl_day', layer : PvForecastBe_05.addSolarLayer('./data/map_daily_' + PvForecastBe_05.myday + '.png', 'sl_day')};
        
        /* add event to the window to keep the map responsive */
        window.addEventListener('resize', function(event){PvForecastBe_05.resizeMap()});
        /* add events to controls */
        $("#btnPrev").click(function() {PvForecastBe_05.plusDivs(-1)});
        $("#btnNext").click (function() {PvForecastBe_05.plusDivs(+1)});
        $("#btnCarousel").click(function() {PvForecastBe_05.toggleCarousel()});
        $("#slide").change(PvForecastBe_05.goToDivs);
        $("#btnSynthesis").click(function() {PvForecastBe_05.showSynthese()});
        PvForecastBe_05.showDivs(PvForecastBe_05.slideIndex);
        PvForecastBe_05.updateSlider(PvForecastBe_05.startHour);
        PvForecastBe_05.startCarousel(); 
//        PvForecastBe_05.showSynthese();
        PvForecastBe_05.resizeMap();        
    },

    // methods
    addPane : function(id, startZi){
        PvForecastBe_05.map.createPane(id);
        PvForecastBe_05.map.getPane(id).style.zIndex = startZi;
    },
    
    addSolarLayer : function(imageUrl, id){
        var SL;
        PvForecastBe_05.addPane(id, 300);
        SL = L.Proj.imageOverlay(imageUrl, PvForecastBe_05.beimgBounds, {pane: id}).addTo(PvForecastBe_05.map);
        return SL
    },
    
    buildMap : function(){
//        PvForecastBe_05.map = L.map('map-container', {center: [50.50, 4.50], zoom: 4, maxBounds: PvForecastBe_05.beBounds, crs: PvForecastBe_05.EPSG31370});
        PvForecastBe_05.map = L.map('map-container', {center: [50.50, 4.50], zoom: 2.7, crs: PvForecastBe_05.EPSG31370});
        PvForecastBe_05.addPane('beadm2', 400);
        PvForecastBe_05.beadm2 = L.Proj.geoJson(PvForecastBe_05.map_be, {weight:0.5, color:"#fff", fill: false, pane: 'beadm2'}).addTo(PvForecastBe_05.map);
        PvForecastBe_05.buildPointsLayer();
        /* Add map event */
        PvForecastBe_05.map.on('popupclose', function(){
            //PvForecastBe_05.map.fitBounds(PvForecastBe_05.beBounds);
            PvForecastBe_05.resizeMap();
        });
        /* Disable dragging around: make a fixed map */
        PvForecastBe_05.map.dragging.disable();
        /* Disable zoom */
        PvForecastBe_05.map.touchZoom.disable();
        PvForecastBe_05.map.doubleClickZoom.disable();
        PvForecastBe_05.map.scrollWheelZoom.disable();
        PvForecastBe_05.map.boxZoom.disable();
        PvForecastBe_05.map.keyboard.disable();
        $(".leaflet-control-zoom").css("visibility", "hidden");        
    },
    
    plageGradient : function(arrElements){
        var grad, nbval, hour, hval, prevhval, nexthval, prevhval2, nexthval2, mycolor;
        nbval = arrElements.length/2;
        grad = '<defs>';
        grad += '<linearGradient id="grad_plage" x1="0%" y1="0%" x2="100%" y2="0%">';
        for (i = 0; i < nbval; i++) {
            hour = arrElements[2*i];
            hval = arrElements[2*i + 1];
            nexthval = arrElements[(2*i + 3)];
            prevhval = arrElements[(2*i - 1)];
            nexthval2 = arrElements[(2*i + 5)];
            prevhval2 = arrElements[(2*i - 3)];
            if (hval == 'M'){
                mycolor = '#cc071e';
            } else if (nexthval == 'M' || prevhval == 'M'){
                mycolor = '#ffe50a';
            } else if (nexthval2 == 'M' || prevhval2 == 'M'){
                mycolor = '#ffe50a';
            } else {
                mycolor = '#f4f3f2';
            }
            grad += '<stop offset="' + ((100 / nbval * (i + 1)) - 7) + '%" style="stop-color:' + mycolor + ';stop-opacity:1" />';
        }
        grad += '</linearGradient>';
        grad += '</defs>';
        
        return grad;        
    },
    
    plageElements : function(arrElements){
        var elements, nbval, hour, hval, prevhval, nexthval, mycolor;
        nbval = arrElements.length/2;
        elements = '';
        for (i = 0; i < nbval; i++) {
            hour = arrElements[2*i];
            if (hour < 10){
                hour = '&nbsp;' + hour;
            }
            hval = arrElements[2*i + 1];
            nexthval = arrElements[(2*i + 3)];
            prevhval = arrElements[(2*i - 1)];
            if (hval == 'M'){
                mycolor = '#ffffff; font-weight:bold';
//            } else if (nexthval == 'M' || prevhval == 'M'){
//                mycolor = '#ffffff';
            } else {
                mycolor = '#58585a';
            }            
            elements += '<text x="' + ((19.5 * i) + 5) + '" y="15" style="fill:' + mycolor + '">' + hour + '</text>';
            elements += '<line x1="' + ((19.5 * (i + 1)) + 2) + '" y1="0" x2="' + ((19.5 * (i + 1)) + 2) + '" y2="20" style="stroke:white;stroke-width:1" />';
        }
        
        return elements;        
    },
        
    buildPlage : function(input){
        var plage, plElements, plLength;
        plElements = $.map( input.split(""), function( a, idx ) {
            var hour;
            if (a == 'o' || a == 'M'){
                hour = idx + PvForecastBe_05.summaryData.utc_offset;
                return [hour, a];
            }            
          });
        plage = '';
        if (plElements.length > 0){
            plLength = plElements.length / 2 * 20;
            plage += '<svg width="' + plLength + '" height="20">';
            plage += PvForecastBe_05.plageGradient(plElements);
            plage += '<rect width="' + plLength + '" height="20" fill="url(#grad_plage)"></rect>';
            plage += PvForecastBe_05.plageElements(plElements);
            plage += '</svg>';
        }        
        return plage;
    },
    
    buildPlagePrev : function(input, hour){
        var plage;       
        if (input.substring(0,1) == 'o'){
            plage = '<svg width="20" height="20">';
            plage += '<rect width="20" height="20" style="fill:#ffe50a" />';
            plage += '<text x="3" y="15" fill="blue">';
            plage += hour
            plage += '</text>';
            plage += '</svg>';
        } else if (input.substring(0,1) == 'M'){
            plage = '<svg width="20" height="20">';
            plage += '<rect width="20" height="20" style="fill:#cc071e" />';
            plage += '<text x="3" y="15" fill="white">';
            plage += hour
            plage += '</text>';
            plage += '</svg>';
        } else {
            plage = '';
        }
        if (0 < input.length){
            plage += PvForecastBe_05.buildPlage(input.substring(1), hour + 1);
        }  
        
        return plage;
    },
    
    buildPointsLayer : function(){
        var myIconPv, totalpv, solpv_points, solpv_layer, myPopup, belCoords, width, point_icon, icon_anchor;
        width = document.documentElement.clientWidth;
        if (width < 600) {
            point_icon = '<img src="./img/puce-petit.png">';
            //point_icon = '<svg height="14" width="14"><circle cx="7" cy="7" r="5" fill="#004677" /></svg>';
            icon_anchor = [8, 14];
        }else{
            point_icon = '<img src="./img/puce-grand.png">';
            //point_icon = '<svg height="25" width="25"><defs><filter id="f2" x="0" y="0" width="200%" height="200%"><feOffset result="offOut" in="SourceAlpha" dx="2" dy="2" /><feGaussianBlur result="blurOut" in="offOut" stdDeviation="3" /><feBlend in="SourceGraphic" in2="blurOut" mode="normal" /></filter></defs><circle cx="10" cy="10" r="8" fill="#004677" filter="url(#f2)" /></svg>';
            icon_anchor = [12, 5];
        }
        
        solpv_points = [];
        $.each(PvForecastBe_05.summaryData.zpoints, function(key, point){ 
            myIconPv = L.divIcon({className: 'geopoint-icon'
                , html: '<a tooltip="'+ point.solptname + '" href="#" class="geopoint">' + point_icon + '<span class="pv-text">' + point.peak + 'h</span></a>'
                , iconAnchor: icon_anchor
                });
            myPopup = L.popup({className:"pv_popup"}).setContent(PvForecastBe_05.buildPopupContent(point));
            belCoords = proj4(PvForecastBe_05.belProjection).inverse([ point.longitude, point.latitude]);
            L.marker([belCoords[1], belCoords[0]],{icon: myIconPv}).bindPopup(myPopup).openPopup().addTo(PvForecastBe_05.map);
        });
    },
    
    buildPopupContent : function(point){
        var htmlContent;
        htmlContent = '<div class="pop_cont">';
        htmlContent += '<div class="pop_title">' + point.solptname.toUpperCase() + '</div>';
        htmlContent += '<div class="pop_clearsky">' + point.clearsky_textual + '</div>';
        htmlContent += '<hr />';
        htmlContent += '<div class="pop_text">';
        htmlContent += '<p>A ' + point.solptname + ', ' + point.clearsky_textual.toLowerCase() + ' ensoleillement pour la saison.</p>';
        htmlContent += '<p> Nous vous conseillons d\'utiliser vos appareils électriques de préférence dans la plage horaire suivante, au plus près du pic de ' + point.peak + 'h.</p>';
        htmlContent += '</div>';
        htmlContent += '<div class="pop_plage">' + PvForecastBe_05.buildPlage(point.graph_plage, PvForecastBe_05.summaryData.utc_offset) + '</div>';
        htmlContent += '</div>';
        return htmlContent;
    },
        
    resizeMap : function () {
        // get the width of the screen after the resize event 
        var width, imggo, imgpause, colorLegend;
        width = document.documentElement.clientWidth;
        // tablets are between 768 and 922 pixels wide
        // phones are less than 768 pixels wide
        if (width > 600 && width < 768) {
            //tablet
            $("#ifr-title h3:first-child").html('<img id="title_icon" src="./img/picto-meteo2.png" alt="pv icon">Électricité solaire - prévisions</h3>');
            $("#btnPrevImg").attr("src", "./img/bout-double-fleche-gauche2.png"); 
            $("#btnNextImg").attr("src", "./img/bout-double-fleche-droit2.png"); 
            $("#btnSynthesisImg").attr("src", "./img/bouton-synthese-petit.png");
            
            $(".geopoint img").attr("src", "./img/puce-grand.png"); 
            imggo = "./img/bout-fleche-2.png";
            imgpause = "./img/bout-pause-2.png";
            
            colorLegend = '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';        
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(78,148,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(78,198,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(21,177,98)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(37,211,24)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(122,237,20)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(218,255,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,229,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,177,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,99,5)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(188,38,13)"></rect>';  
            colorLegend += '</svg>';  
            
            
            PvForecastBe_05.map.fitBounds(PvForecastBe_05.beBounds);
        } else if (width > 768) {
            //large screen
            $("#ifr-title h3:first-child").html('<img id="title_icon" src="./img/picto-meteo2.png" alt="pv icon">Électricité solaire - prévisions</h3>');
            $("#btnPrevImg").attr("src", "./img/bout-double-fleche-gauche2.png"); 
            $("#btnNextImg").attr("src", "./img/bout-double-fleche-droit2.png"); 
            $("#btnSynthesisImg").attr("src", "./img/bouton-synthese.png");
            $(".geopoint img").attr("src", "./img/puce-grand.png"); 
            imggo = "./img/bout-fleche-2.png";
            imgpause = "./img/bout-pause-2.png";
            
            colorLegend = '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';        
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(78,148,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(78,198,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(21,177,98)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(37,211,24)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(122,237,20)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(218,255,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,229,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,177,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(255,99,5)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.84em" height="1.0874em">';            
            colorLegend += '    <rect width="1.84em" height="1.0874em" style="fill:rgb(188,38,13)"></rect>';  
            colorLegend += '</svg>';  
            
            PvForecastBe_05.map.fitBounds(PvForecastBe_05.beBounds);
        } else {
            // console.log('smartphone');
            $("#title_icon").attr("src", "./img/picto-meteo1.png");
            $("#ifr-title h3:first-child").html('<div><div style="position: relative; float: left;"><img id="title_icon" src="./img/picto-meteo1.png" alt="pv icon"></div> <div style="text-align:center;line-height: 1.0;">Électricité solaire prévisions</div></div>');
            $("#btnPrevImg").attr("src", "./img/bout-double-fleche-gauche1.png"); 
            $("#btnNextImg").attr("src", "./img/bout-double-fleche-droit1.png");
            $("#btnSynthesisImg").attr("src", "./img/bouton-synthese-petit.png");
            $(".geopoint img").attr("src", "./img/puce-petit.png"); 
            imggo = "./img/bout-fleche-1.png";
            imgpause = "./img/bout-pause-1.png";
            
            colorLegend = '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';        
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(78,148,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(78,198,228)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(21,177,98)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(37,211,24)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(122,237,20)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(218,255,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(255,229,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(255,177,10)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(255,99,5)"></rect>';  
            colorLegend += '</svg>';  
            colorLegend += '<svg title="Légende de la carte" width="1.3383333467168em" height="0.836458341698em">';            
            colorLegend += '    <rect width="1.3383333467168em" height="0.836458341698em" style="fill:rgb(188,38,13)"></rect>';  
            colorLegend += '</svg>';  
            
            PvForecastBe_05.map.setView([50.50, 4.50], 2.7);
        }
        $("#ifr-legend-colors").html(colorLegend);
        if(PvForecastBe_05.timer == 0){
            $("#btnCarouselImg").attr("src", imggo);            
        } else{
            $("#btnCarouselImg").attr("src", imgpause);          
        }
    },
    
    plusDivs : function (n) {
        PvForecastBe_05.showDivs(PvForecastBe_05.slideIndex += n);
    },

    goToDivs : function () {
        var n;
        n = $("#slide").val();
        PvForecastBe_05.slideIndex = n - PvForecastBe_05.startHour + 1;
        PvForecastBe_05.showDivs(PvForecastBe_05.slideIndex);
    },

    showDivs : function (n) {
        var i, x = PvForecastBe_05.sl;
        if (n > x.length-1) {
            PvForecastBe_05.slideIndex = 1
        }
        if (n < 1) {
            PvForecastBe_05.slideIndex = x.length-1
        }
        ;
        for (i = 0; i < x.length; i++) {
            PvForecastBe_05.map.getPane(x[i].id).style.zIndex = 300;
        }
        PvForecastBe_05.map.getPane(x[PvForecastBe_05.slideIndex - 1].id).style.zIndex = 301;
        PvForecastBe_05.updateSlider(PvForecastBe_05.slideIndex + PvForecastBe_05.startHour - 1);
    },
    
    showSynthese : function(){
        var i, x = PvForecastBe_05.sl;
        PvForecastBe_05.stopCarousel();
        for (i = 0; i < x.length; i++) {
            PvForecastBe_05.map.getPane(x[i].id).style.zIndex = 300;
        }
        PvForecastBe_05.map.getPane('sl_day').style.zIndex = 301;
        PvForecastBe_05.updateSlider(99);
    },
    
    startCarousel : function () {
        var i, x = PvForecastBe_05.sl;
        for (i = 0; i < x.length; i++) {
            PvForecastBe_05.map.getPane(x[i].id).style.zIndex = 300;
        }
        PvForecastBe_05.slideIndex++;
        if (PvForecastBe_05.slideIndex > x.length-1) {
            PvForecastBe_05.slideIndex = 1
        }
        PvForecastBe_05.map.getPane(x[PvForecastBe_05.slideIndex - 1].id).style.zIndex = 301;
        PvForecastBe_05.updateSlider(PvForecastBe_05.slideIndex + PvForecastBe_05.startHour - 1);
        PvForecastBe_05.timer=setTimeout(PvForecastBe_05.startCarousel, 1000);
    },

    stopCarousel : function () {
        clearTimeout(PvForecastBe_05.timer);
        PvForecastBe_05.timer = 0;
    },
    
    toggleCarousel : function () {
        var width, imggo, imgpause;
        width = document.documentElement.clientWidth;
        if (width < 600) {
            imggo = "./img/bout-fleche-1.png";
            imgpause = "./img/bout-pause-1.png";
        }else{
            imggo = "./img/bout-fleche-2.png";
            imgpause = "./img/bout-pause-2.png";
        }
        
        if(PvForecastBe_05.timer == 0){
            PvForecastBe_05.startCarousel();
            $("#btnCarouselImg").attr("src", imgpause);            
        } else{
            PvForecastBe_05.stopCarousel();
            $("#btnCarouselImg").attr("src", imggo);          
        }
    },
    
    updateSlider : function (slideAmount) {
        var width, imggo, imgpause;
        width = document.documentElement.clientWidth;
        if (width < 600) {
            imggo = "./img/bout-fleche-1.png";
            imgpause = "./img/bout-pause-1.png";
        }else{
            imggo = "./img/bout-fleche-2.png";
            imgpause = "./img/bout-pause-2.png";
        }
        if(slideAmount==99){
            // hide the slider      
            $("#slidevalue").html("");
            $("#slide").hide();
            // btn carousel stopped
            $("#btnCarouselImg").attr("src", imggo);
        }else{
            // show the slider
            $("#slide").show();
            $("#slidevalue").html(slideAmount +  + PvForecastBe_05.summaryData.utc_offset + 'h');
            // move the cursor at the right value        
            $("#slide").val(slideAmount);
        }
    }
};

/**
 * Load administrative geojson map and json data before activating the page
 * This can be modified adding a varaible declaration in the json file and loading it as a script
 */
var myday = $.urlParam('myday');

$.getJSON( "./js/aaageo2.json", function( mapjson ) {
    PvForecastBe_05.map_be = mapjson;
    $.getJSON( "./data/summary_daily_" + myday + ".json", function( datajson ) {
        PvForecastBe_05.summaryData = datajson;
        PvForecastBe_05.onReady();
       });
});
