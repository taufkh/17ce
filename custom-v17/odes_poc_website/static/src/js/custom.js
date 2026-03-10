/** @odoo-module **/

// NOTE: Cookies global is provided by js-cookie.js loaded before this file.

function getUrlVars() {
    var vars = {};
    window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function (m, key, value) {
        vars[key] = value;
    });
    return vars;
}

$(document).ready(function () {
    // Cookie acceptance bar
    function odes_cookieAcceptBar() {
        var showpopup = Cookies.get("odes_cookieAcceptBar");
        if (showpopup !== "active") {
            var $bar = $("#odes_cookieAcceptBar");
            $bar.show();
            $bar.find(".cookieAcceptBarConfirm").on("click", function () {
                Cookies.set("odes_cookieAcceptBar", "active", { expires: 1 });
                $bar.fadeOut();
            });
        }
    }
    odes_cookieAcceptBar();

    // Pre-fill hidden social_media field from URL param
    if ($(".odes_crm_social_media").length) {
        var urlVars = getUrlVars();
        if ("social_media" in urlVars) {
            $(".odes_crm_social_media").val(urlVars["social_media"]);
        }
    }

    // Dynamic sub-category checkboxes when form category changes
    $("body").on("change", '.s_website_form_rows [name="category"]', function () {
        var value = $(this).val();
        $(".sales_teams_submodule").hide();

        $.ajax({
            type: "post",
            url: "/list/search",
            data: { sales_id: value },
            dataType: "json",
            cache: false,
            success: function (data) {
                var datas = data["datas"];
                var html = '<ul class="ks-cboxtags">';
                for (var i = 0; i < datas.length; i++) {
                    html +=
                        "<li>" +
                        '<input type="checkbox" id="category_childs_' + datas[i]["id"] +
                        '" name="category_childs" value="' + datas[i]["id"] + '"/>' +
                        '<label for="category_childs_' + datas[i]["id"] + '">' +
                        datas[i]["name"] + "</label>" +
                        "</li>";
                }
                html += "</ul>";
                $(".sales_teams_child").html(html);
                if (datas.length > 0) {
                    $(".sales_teams_submodule").show();
                }
            },
            error: function () {
                console.error("An error occurred fetching sales sub-categories.");
            },
        });
    });
});
