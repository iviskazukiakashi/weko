$(document).ready(function () {
  $("#api_account_save").prop("disabled", true);

  $("#input_type").change(function (e) {
    let value = $("#input_type").val();
    if (value == "0") {
      $("#CrossRef_API").addClass("hidden");
      $("#api_account_save").prop("disabled", true);
    } else {
      $("#api_account_save").prop("disabled", false);
      if (value == "crf") {
        $("#CrossRef_API").removeClass("hidden");
      }
      loadCurrentCertData();
    }
  });

  loadDataForInputType();

  $("#api_account_save").click(function (e) {
    save();
  });
});

function addAlert(message) {
    $('#alerts').append(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
         }

var save = function () {
  let api_code = $.trim($('#input_type').val());
  let cert_data = $.trim($('#cross_ref_account').val());
  if (!api_code || api_code == '0'){
    //alert('Input type is invalid. Please check again.');
    var modalcontent =  "Input type is invalid. Please check again.";
    $("#inputModal").html(modalcontent);
    $("#allModal").modal("show");
    return;
  } else if(!cert_data){
    //alert('Account information is invalid. Please check again.');
    var modalcontent =  "Account information is invalid. Please check again.";
    $("#inputModal").html(modalcontent);
    $("#allModal").modal("show");
    return;
  }
  let param = {
    "api_code": api_code,
    "cert_data": cert_data
  }
  $.ajax({
    url: "/api/admin/save_api_cert_data",
    type: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    data: JSON.stringify(param),
    dataType: 'json',
    success: function (data, status) {
      let err_msg = data.error;
      if (err_msg) {
        //alert(err_msg);
        var modalcontent = err_msg;
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
      } else if (!data.results) {
        //alert('Account information is invalid. Please check again.');
        var modalcontent =  "Account information is invalid. Please check again.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
      } else {
        addAlert('Account info has been saved successfully.');
      }
    },
    error: function (error) {
        //alert(error);
        var modalcontent = error;
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
    }
  });
}

var loadDataForInputType = function () {
  $.ajax({
    url: "/api/admin/get_api_cert_type",
    type: 'GET',
    success: function (data) {
      let error = data.error;
      let results = data.results;
      if (error) {
        //alert(error);
        var modalcontent = error;
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return;
      }
      if (!results) {
        //alert('Not found certificate data.');
        var modalcontent =  "Not found certificate data.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return;
      }
      let options = '';
      for (let i = 0; i < results.length; i++) {
        options += '<option value="' + results[i].api_code + '">' + results[i].api_name + '</option>';
      }
      const select = $('#input_type');
      select.append(options);
    },
    error: function (error) {
      //alert('Error when load account info.');
        var modalcontent = "Error when load account info.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
    }
  });
}

var loadCurrentCertData = function () {
  const currentTime = new Date().getTime();
  let get_url = "/api/admin/get_curr_api_cert/" + $('#input_type').val() + '?time=' + currentTime;
  $.ajax({
    url: get_url,
    type: 'GET',
    success: function(data, status)  {
      $('#cross_ref_account').val(data.results.cert_data);
    },
    error: function (error) {
      //alert('Error when load certificate data of ' + $('#input_type').val());
        var modalcontent = "Error when load certificate data of " + $("#input_type").val();
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
    }
  });
}
