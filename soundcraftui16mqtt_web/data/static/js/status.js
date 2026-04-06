function request_database_update(msg, topic){
  var message = new Paho.Message(msg);
  message.destinationName = "database_request/" + window.mqtt_client.clientId + "/" + topic;
  window.mqtt_client.send(message);
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
  $("#btn-mqtt").removeClass("btn-success").addClass("btn-danger");
}

function onConnect() {
  window.mqtt_client.subscribe("webpage/#");
  console.log("Mqtt Client connected");
  $("#btn-mqtt").removeClass("btn-danger").addClass("btn-success");
}

function onMessageArrived(message) {
  console.log("Message arrived on topic " + message.destinationName + " with content " + message.payloadString);
}
