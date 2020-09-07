function updateConfig(gid) {
	var text = ace.edit("e").getValue();

	$("#success").addClass("d-none");
	$("#error").addClass("d-none");
	$("#malformed-config").addClass("d-none");
	$("#not-editor").addClass("d-none");

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
			if (res.status === 400) {
				return $("#malformed-config").removeClass("d-none");
			} if (res.status === 403) {
				return $("#not-editor").removeClass("d-none");
			}

			$("#error").removeClass("d-none");
			console.error(`Failed to update: ${res}`)
        }
    });
}