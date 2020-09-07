function updateConfig(gid) {
	var text = ace.edit("e").getValue();

	$("#success").addClass("d-none");
	$("#error").addClass("d-none");

	$.ajax({
        url: `/api/${gid}/config`,
        type: "PUT",
        contentType: "application/json",
        data: JSON.stringify({
			newConfig: text
		}),
        success: function(res) {
			$("#success").removeClass("d-none");
        },
        error: function(res) {
			$("#error").removeClass("d-none");
			console.error(`Failed to update: ${res}`)
        }
    });
}