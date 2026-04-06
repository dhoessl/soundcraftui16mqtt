function send_message(msg, topic){
  var message = new Paho.Message(msg);
  message.destionationName = "database_request/" + window.mqtt_client.clientId + "/" + topic;
  window.mqtt_client.send(message);
}

function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  window.mqtt_client.subscribe("database_update/all/#");
  window.mqtt_client.subscribe("database_update/" + window.mqtt_client.clientId + "/#");
  window.mqtt_client.subscribe("webpage/#");
  console.log("Mqtt Client connected");
  $("#btn-mqtt").removeClass("btn-danger").addClass("btn-success");
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
  $("#btn-mqtt").removeClass("btn-success").addClass("btn-danger");
}
function onMessageArrived(message) {
  console.log("Message arrived on topic " + message.destionationName + " with content " + message.payloadString);
}

window.addEventListener("load", function(){
  broker_host = $("#mqtt_data").attr("host");
  broker_port = $("#mqtt_data").attr("port");
  var client = new Paho.Client(broker_host, Number(broker_port), uuid4());
  window.mqtt_client = client;

  // set callback handlers
  window.mqtt_client.onConnectionLost = onConnectionLost;
  window.mqtt_client.onMessageArrived = onMessageArrived;

  // connect the client
  window.mqtt_client.connect({onSuccess:onConnect});

});
