/**
 * Created with PyCharm.
 * User: xulei
 * Date: 3/14/13
 * Time: 11:20 AM
 * For creating and dropping monitor timer task
 */
var Timer = {
    /** field **/
    _timer_pool:new Map(),
    _tag_array:new Array(),
    _options:{
        period:60000
    },

    /** method **/
    initialize:function (options) {
        this._options.period = options.period;
    },

    createPool:function (navTabId) {
        if (!navTabId) return;
        this._timer_pool.put(navTabId, new Array());
    },

    submit:function (navTabId, func, options) {
        var period = this._options.period;
        var hasTag = false;
        if (options) {
            period = options.period;
            hasTag = options.tag;
        }

        var invokeList = this._get(navTabId);
        if (!invokeList) {
            invokeList = new Array();
            this._timer_pool.put(navTabId, invokeList);
        }
        var pid = window.setInterval(func, period);
        invokeList.push(pid);
        if (hasTag) {
            this._tag_array.push({pid:pid, tag:options.tag})
        }
    },

    cancel:function (navTabId) {
        var invokeList = this._get(navTabId);
        if (!invokeList) {
            console.log("No task need to be canceled.");
        }
        var length = invokeList.length;
        for (var i = 0; i < length; i++) {
            window.clearInterval(invokeList.pop());
        }
        // only clear array
        this._tag_array.splice(0, this._tag_array.length);
    },

    cancelTag:function (tag) {
        var array = this._tag_array.slice(0);
        var length = array.length;
        var entry = null;
        for (var i = 0; i < length; i++) {
            entry = array.shift();
            if (entry.tag == tag) {
                window.clearInterval(entry.pid);
                this._tag_array.shift();
            }
        }
    },

    _get:function (navTabId) {
        if (!navTabId) return null;
        return  this._timer_pool.get(navTabId);
    }
};