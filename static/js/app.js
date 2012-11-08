$(document).ready(function(){
	//bind approve click handler
	$('.approve').click(function(){
		// post request to server containing ID
		var yes=confirm("Sure you want to approve this?");
		if(yes==true){
			//post
			var pathname = window.location.pathname;
			var data = {entry_id:$(this).attr('class').split(/\s+/).slice(-1)[0]};
			var herp = $(this);
			$.post(pathname,data,function(d,st,xr){
				console.log("Successful approve");
				herp.parent().remove();
			});
		}
		else{
			console.log("Doing nothing.");
		}
	});

	//bind upvote click handler
	$('.upvote').click(function(){
		// post request to server containing ID
		var pathname = window.location.pathname;
		var classes = $(this).attr('class').split(/\s+/);
		var entry = classes.slice(-1)[0]
		var data = {del:'false',entry_id:entry};
		var herp = $(this);
		$.post(pathname,data,function(d,st,xr){
			console.log("Successful upvote");
			herp.text((parseInt(herp.text())+1).toString());
		});
	});


	//bind delete click handler
	$('.delete').click(function(){
		// post request to server containing ID
		var yes=confirm("Sure you want to delete?");
		if(yes==true){
			var pathname = window.location.pathname;
			var classes = $(this).attr('class').split(/\s+/);
			var entry = classes.slice(-1)[0]
			var data = {del:'true',entry_id:entry};
			var herp = $(this);
			$.post(pathname,data,function(d,st,xr){
				console.log("Successful delete");
				herp.parent().remove();
			});
		}
		else{
			console.log("Doing nothing.");
		}
	});
});