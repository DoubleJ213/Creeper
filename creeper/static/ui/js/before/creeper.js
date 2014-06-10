
/*
 * obj : the select all checkbox action checkbox
 * checkbox_name : one checkbox name attribute
 */
function checkbox_select_all(obj, checkbox_name) {
    $("input[name=" + checkbox_name + "]").each(function () {
        $(this).attr("checked", obj.checked);
    });
}

function judge_select_all_checkbox(checkbox_all_id, checkbox_name) {
    var checked_len = $("input[name=" + checkbox_name + "]:checked").length;
    var all_len = $("input[name=" + checkbox_name + "]").length;
    if (checked_len != all_len) {
        $("#" + checkbox_all_id).attr("checked", false);
    } else {
        $("#" + checkbox_all_id).attr("checked", true);
    }
}

//instance list more function

//Stop generate bubble
function getEventObj(){
    if(window.event){
        return window.event;
    }else{
        var obj = getEventObj.caller;
        while(obj != null){
            var arg = obj.arguments[0];
            if(arg){
                if((arg.constructor == Event || arg.constructor == MouseEvent || arg.constructor == KeyboardEvent)
                    || (typeof(arg) == "object" && arg.preventDefault && arg.stopPropagation)){
                    return arg;
                }
            }
            obj = obj.caller;
        }
    }
}
function stopBubble(){
    var e = getEventObj();
    if(window.event){
        e.cancelBubble = true;
    }else if(e.preventDefault){
        e.stopPropagation();
    }
}

function instance_list_new(tr_obj,instance_div,position_id){
    var xx = 0,yy = 0;
    var div_db = $("#"+position_id);
    var window_width=$(window).width();
    var instance_div = $("#"+instance_div);
    div_db.html(instance_div.html());
    instance_div.show();
    $(tr_obj).click(function(e){
        xx = e.clientY;
        yy = e.clientX;
        var brow = $.browser;
        if(brow.msie){
            div_db.css({top:(xx-155)+ "px",right:(window_width - yy - 2)+"px"});
        }
        else{
            div_db.css({top:(xx-100)+ "px",right:(window_width - yy - 2)+"px"});
        }
        div_db.show();
    });
    div_db.bind('mouseover',function(){
        $(this).show();
    });
    div_db.bind('mouseout',function(){
        $(this).hide();
    });
    $("a[target=dialog]", $("#"+position_id)).each(function(){
        $(this).click(function(event){
            var $this = $(this);
            var title = $this.attr("title") || $this.text();
            var rel = $this.attr("rel") || "_blank";
            var options = {};
            var w = $this.attr("width");
            var h = $this.attr("height");
            if (w) options.width = w;
            if (h) options.height = h;
            options.max = eval($this.attr("max") || "false");
            options.mask = eval($this.attr("mask") || "false");
            options.maxable = eval($this.attr("maxable") || "true");
            options.minable = eval($this.attr("minable") || "true");
            options.fresh = eval($this.attr("fresh") || "true");
            options.resizable = eval($this.attr("resizable") || "true");
            options.drawable = eval($this.attr("drawable") || "true");
            options.close = eval($this.attr("close") || "");
            options.param = $this.attr("param") || "";

            var url = unescape($this.attr("href")).replaceTmById($(event.target).parents(".unitBox:first"));
            DWZ.debug(url);
            if (!url.isFinishedTm()) {
                alertMsg.error($this.attr("warn") || DWZ.msg("alertSelectMsg"));
                return false;
            }
            $("#display_div").hide();
            $.pdialog.open(url, rel, title, options);

            return false;
        });
    });
    $("a[target=navTab]", $("#"+position_id)).each(function(){
        $(this).click(function(event){
            var $this = $(this);
            var title = $this.attr("title") || $this.text();
            var tabid = $this.attr("rel") || "_blank";
            var fresh = eval($this.attr("fresh") || "true");
            var external = eval($this.attr("external") || "false");
            var url = unescape($this.attr("href")).replaceTmById($(event.target).parents(".unitBox:first"));
            DWZ.debug(url);
            if (!url.isFinishedTm()) {
                alertMsg.error($this.attr("warn") || DWZ.msg("alertSelectMsg"));
                return false;
            }
            $("#display_div").hide();
            navTab.openTab(tabid, url,{title:title, fresh:fresh, external:external});

            event.preventDefault();
        });
    });
}

function instance_list_hide(position_id){
    $("#"+position_id).hide();
}
