function getBrowserLanguage(){
    var browserLang = window.navigator.language;
    if(!browserLang){
        browserLang = window.navigator.browserLanguage;
    }
    browserLang = browserLang.toLowerCase();
    return browserLang;
}