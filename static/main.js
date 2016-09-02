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

function turnDivToTextArea(commentId){
	// Make Save Link visible
	$('#save' + commentId).show();

	// Save Text Data
	var divHtml = $("#" + commentId).html().trim();
	console.log(divHtml);

	// Create Dynamic Text area
	var editableText = $("<textarea class=\"col-xs-12 comment\" name=\"mycomment\" value={{newcomment}}/>");

	// Fill Text area
	editableText.val(divHtml);

	// Replace Div with Text Area
	$("#" + commentId).replaceWith(editableText);

	// Focus
	editableText.focus();
}