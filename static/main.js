function redirectOnClick(blogId){
	window.location = "/blog/" + blogId;
}

function logoff(){
	window.location = "/logoff";
}

function signup(){
	window.location = "/signup";
}

function login(){
	window.location = "/login";
}

function deletePost(postId){
	window.location = "/blog/delete/" + postId;
}

function editPost(postId){
	window.location = "/blog/edit/" + postId;
}

function toggleCommentsVisibility(){
	if ($('#addcommentsection').css('display') == 'none'){
		$('#addcommentsection').show();
	}
	else{
		$('#addcommentsection').hide();
	}
}