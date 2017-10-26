function checkFlag() {
  console.log("Checking Flag")
  flag = $("#flag").val()
  console.log("Flag Input: ",flag)
  if( flag == "") {
    console.log("Invalid Flag Input")
    $("#validityText").html("Invalid Flag Input");
    return;
  }
  flagValid = $.ajax({
    dataType: 'json',
    url: document.URL,
    method: "POST",
    data: {"flag" : flag}
  });
  flagValid.done(function(recvd){
    if(recvd.correct == 1) {
      console.log("Flag Correct")
      $("#validityText").html("Flag Correct");
    }
    else if(recvd.correct == 0) {
      console.log("Flag Incorrect")
      $("#validityText").html("Flag Incorrect");
    }
  });
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js').then(function(registration) {
      // Registration was successful
      console.log('ServiceWorker registration successful with scope: ', registration.scope);
    }, function(err) {
      // registration failed :(
      console.log('ServiceWorker registration failed: ', err);
    });
  });
}

window.addEventListener('beforeinstallprompt', function(e) {
  console.log('beforeinstallprompt Event fired');
  e.preventDefault();
  return false;
});
