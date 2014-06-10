function gotoUrl(htmlObj,url,nextObj,next_url,liObj,liIdVal){
    showBackground();
    if($(nextObj)){
        $(nextObj).val(next_url);
    }
    if($(liObj)){
        $(liObj).val(liIdVal);
    }
    if($("body").data("proTreeDialogId")){
        $.pdialog.closeCurrent();
    }
    if(url!=null && url!=''){
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'html',
            cache: false,
            success: function(htmlData){
                $(htmlObj).html(htmlData).initUI();
                hideBackground();
            },
            error: DWZ.ajaxError
        });
    }else{
        hideBackground();
    }
}

function showBackground(){
    if($("#progressBar")){
        $("#progressBar").css("display","block");
    }
    if($("#background")){
        $("#background").css("display","block");
    }
}

function hideBackground(){
    if($("#progressBar")){
        $("#progressBar").css("display","none");
    }
    if($("#background")){
        $("#background").css("display","none");
    }
}

function openProDialog(url, dlgId, title, width, height, nextObj, next_url, liObj, liIdVal){
    if($("#project_rightDiv")){
        $("#project_rightDiv").html('');
    }
    if($(nextObj)){
        $(nextObj).val(next_url);
    }
    if($(liObj)){
        $(liObj).val(liIdVal);
    }
    $.pdialog.open(url, dlgId, title, {width: width, height: height});
}

function get_display_name(name,maxLen) {
    var morelength = getMoreBytesCount(name);
    var len = name.length + morelength;
    if(len > maxLen){
        var str1 = name.replace(/([\u0391-\uffe5])/ig,"$1a");
        var str2 = str1.substring(0,maxLen-1);
        name = str2.replace(/([\u0391-\uffe5])a/ig,"$1");
        name = name + "...";
    }
    return name;

}
function getMoreBytesCount(str){
    if(str == null){
        return 0;
    }else{
        return(str.replace(/[\u0000-\u00ff]/g,"").length);
    }
}
