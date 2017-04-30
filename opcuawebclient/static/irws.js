// InRunan WebSocket Event
(function(B) {
	B.IRWS = function(options){
		options = options || {};
		var ws = new WebSocket((options.wsurl || "ws://"+window.location.host+"/ws/") + (options.channel || "default"));
		var thiz = this;
		thiz.ws = ws;
		thiz.isopen = false;
		// 打开Socket
		thiz.queue = [];
		thiz.subscribeMap = {};
		['onopen', 'onclose', 'onerror'].forEach(function(m){
			if(options[m]){
				thiz[m] = options[m];
			}
		});
		thiz.checkQueue = function(){
			while(thiz.queue.length){
				var msg = thiz.queue.shift();
				ws.send(msg);
			}
		};
		ws.onerror = function(){
			if(thiz.onerror)
				thiz.onerror();
		};
		thiz.rawsend = function(data){
			if(thiz.isclose)
				throw "websocket closed";
			var msg = JSON.stringify(data);
			if(thiz.isopen){
				thiz.checkQueue();
				ws.send(msg);
			}
			else{
				thiz.queue.push(msg);
			}
		};
		thiz.subscribe = function(tag, callback){
			if(!tag)
				tag = 'default';
			if(!(tag in thiz.subscribeMap)){
				thiz.subscribeMap[tag] = [];
			}
			thiz.subscribeMap[tag].push(callback);
			thiz.rawsend({
				type:'subscribe', tag:tag
			});
		};
		thiz.send = function(data, tag){
			thiz.rawsend({
				type:'data', tag:tag || 'default', data:data
			});
		};
		ws.onopen = function(event) {
			thiz.isopen = true;
			thiz.checkQueue();
			ws.onclose = function(event) {
				thiz.isclose = true;
				thiz.isopen = false;
				if(thiz.onclose){
					thiz.onclose();
				}
			}; 
			ws.onmessage = function(event) { 
				var data = JSON.parse(event.data);
				if(data.type == "data"){
					var tag = data.tag;
					if(thiz.subscribeMap[tag]){
						thiz.subscribeMap[tag].forEach(function(callback){
							callback(data.data);
						})
					}
				}
				else if(data.type == "subscribe"){
					thiz.cid = data.data.cid;
				}
			};
			if(thiz.onopen){
				thiz.onopen();
			}
		};
		thiz.close = function(){
			ws.close();
		};
	};
})(window)
