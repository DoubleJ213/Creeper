
(function($){
	$.fn.extend({
		theme: function(options){
			var op = $.extend({themeBase:"themes"}, options);
			var _themeHref = "/static/ui/"+op.themeBase + "/#theme#/style.css";
			return this.each(function(){
				var jThemeLi = $(this).find(">li[theme]");
				var setTheme = function(themeName){
//					$("head").find("link[href$='style.css']").attr("href", _themeHref.replace("#theme#", themeName));

                    var target;

                    var head=$("head").children().length;
                    target = head == 0?"body":"head";

                    if(window.navigator.userAgent.indexOf("MSIE")>0){
                        $(target).find("link[href$='style.css']").attr("href", _themeHref.replace("#theme#", themeName));
                        $(target).find("link[href$='style.css']").attr("href", _themeHref.replace("#theme#", themeName));
                    }else{
                        $(target).find("link[href$='style.css']:eq(0)").remove();
                        var styleHref = _themeHref.replace("#theme#", themeName);
                        var linkObj = "<link href=\""+styleHref+"\" rel=\"stylesheet\" type=\"text/css\" media=\"screen\"/>";
                        $(target).find("link[href$='core.css']").before(linkObj);
                    }

					jThemeLi.find(">div").removeClass("selected");
					jThemeLi.filter("[theme="+themeName+"]").find(">div").addClass("selected");
					if ($.isFunction($.cookie)) $.cookie("dwz_theme", themeName);
				}
				
				jThemeLi.each(function(index){
					var $this = $(this);
					var themeName = $this.attr("theme");
					$this.addClass(themeName).click(function(){
						setTheme(themeName);
					});
				});
				if ($.isFunction($.cookie)){
					var themeName = $.cookie("dwz_theme");
					if (themeName) {
						setTheme(themeName);
					}
				}
			});
		}
	});
})(jQuery);
